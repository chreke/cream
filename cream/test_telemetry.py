"""Bounded, isolated capture tests: no application server or live ingest key."""

import os
import subprocess
import sys
import textwrap

import pytest


def run_isolated(source, **env):
    result = subprocess.run(
        [sys.executable, '-c', textwrap.dedent(source)],
        env={
            **os.environ,
            'DJANGO_SETTINGS_MODULE': 'cream.settings',
            'DEBUG': '1',
            'ALLOWED_HOSTS': 'testserver',
            'POSTGRES_DB': 'unused',
            'POSTGRES_USER': 'unused',
            'POSTGRES_PASSWORD': '',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'AIENT_PUBLISHABLE_KEY': '',
            'OTEL_SDK_DISABLED': 'false',
            **env,
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('disabled', [False, True])
def test_telemetry_is_opt_in(disabled):
    run_isolated('''
        import logging
        from opentelemetry import trace
        from cream.telemetry import configure_telemetry, configure_logging
        before = list(logging.getLogger().handlers)
        configure_telemetry()
        configure_logging()
        assert list(logging.getLogger().handlers) == before
        assert not trace.get_tracer(__name__).start_span('disabled').is_recording()
    ''', AIENT_PUBLISHABLE_KEY='test-only' if disabled else '',
        OTEL_SDK_DISABLED=str(disabled).lower())


def test_rejects_non_full_release_sha():
    run_isolated('''
        from cream.telemetry import configure_telemetry
        try:
            configure_telemetry()
        except ValueError as exc:
            assert 'COMMIT_SHA' in str(exc)
        else:
            raise AssertionError('short release commit was accepted')
    ''', AIENT_PUBLISHABLE_KEY='test-only', COMMIT_SHA='abc123')


def test_default_service_omits_unavailable_release_metadata():
    run_isolated('''
        from opentelemetry import trace
        from cream.telemetry import configure_telemetry
        configure_telemetry()
        attrs = trace.get_tracer_provider().resource.attributes
        assert attrs['service.name'] == 'cream'
        assert not any(name.startswith('release.') for name in attrs)
        assert 'deployment.commit_sha' not in attrs
        trace.get_tracer_provider().shutdown()
    ''', AIENT_PUBLISHABLE_KEY='test-only', COMMIT_SHA='', COMMIT_REF='',
        AIENT_ENV='', OTEL_SERVICE_NAME='', OTEL_RESOURCE_ATTRIBUTES='')


@pytest.mark.parametrize('entrypoint', ['wsgi', 'asgi'])
def test_bootstrap_exports_correlated_otlp_logs_and_spans(entrypoint):
    run_isolated('''
        import asyncio
        import importlib
        import logging
        import os
        import sys
        import types
        from unittest.mock import patch

        import requests
        from opentelemetry import trace
        from opentelemetry._logs import get_logger_provider
        from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

        captured = []
        def send(session, request, **kwargs):
            captured.append(request)
            response = requests.Response()
            response.status_code = 200
            response._content = b''
            return response

        # This process is disposable. Keep capture active through atexit too,
        # so a failed assertion can never send shutdown telemetry to a network.
        patch.object(requests.Session, 'send', send).start()
        def capture_pipeline():
            bootstrap = importlib.import_module('cream.' + os.environ['ENTRYPOINT'])
            from cream.telemetry import configure_telemetry, configure_logging
            from django.conf import settings
            from django.contrib.auth.decorators import login_not_required
            from django.http import HttpResponse
            from django.test import Client, AsyncClient
            from django.urls import path

            handlers = list(logging.getLogger().handlers)
            configure_telemetry()
            configure_logging()
            assert logging.getLogger().handlers == handlers
            assert settings.MIDDLEWARE.count(
                'opentelemetry.instrumentation.django.middleware.otel_middleware._DjangoMiddleware'
            ) == 1

            @login_not_required
            def probe(request):
                logging.getLogger('cream.capture').warning(
                    'bounded capture', extra={'request': request},
                )
                return HttpResponse('ok')

            urls = types.ModuleType('capture_urls')
            urls.urlpatterns = [path('probe/', probe)]
            sys.modules[urls.__name__] = urls
            settings.ROOT_URLCONF = urls.__name__

            if os.environ['ENTRYPOINT'] == 'asgi':
                async def capture():
                    client = AsyncClient()
                    for _ in range(2):
                        assert (await client.get('/probe/')).status_code == 200
                asyncio.run(capture())
            else:
                client = Client()
                for _ in range(2):
                    assert client.get('/probe/').status_code == 200

            # Exporter diagnostics must not recursively export themselves.
            logging.getLogger('opentelemetry.capture').warning('not exported')
            assert trace.get_tracer_provider().force_flush(timeout_millis=5000)
            assert get_logger_provider().force_flush(timeout_millis=5000)
            get_logger_provider().shutdown()
            trace.get_tracer_provider().shutdown()

        capture_pipeline()
        spans, logs, resources = [], [], []
        for request in captured:
            assert request.headers['Authorization'] == 'Bearer test-only'
            assert request.headers['Content-Type'] == 'application/x-protobuf'
            if request.url == 'https://capture.invalid/v1/traces':
                message = ExportTraceServiceRequest.FromString(request.body)
                for resource in message.resource_spans:
                    resources.append(resource.resource)
                    for scope in resource.scope_spans:
                        spans.extend(scope.spans)
            elif request.url == 'https://capture.invalid/v1/logs':
                message = ExportLogsServiceRequest.FromString(request.body)
                for resource in message.resource_logs:
                    resources.append(resource.resource)
                    for scope in resource.scope_logs:
                        logs.extend(scope.log_records)
            else:
                raise AssertionError(request.url)

        assert len(spans) == len(logs) == 2, (len(spans), len(logs))
        assert all(log.body.string_value == 'bounded capture' for log in logs)
        assert all(attr.key != 'request' for log in logs for attr in log.attributes)
        assert {log.trace_id for log in logs} == {span.trace_id for span in spans}
        assert {log.span_id for log in logs} == {span.span_id for span in spans}
        for resource in resources:
            attrs = {attr.key: attr.value.string_value for attr in resource.attributes}
            assert attrs['service.name'] == 'cream-test'
            assert attrs['release.commit'] == attrs['deployment.commit_sha'] == 'a' * 40
            assert attrs['release.branch'] == attrs['deployment.commit_ref'] == 'main'
            assert attrs['release.environment'] == attrs['deployment.environment'] == 'test'
            assert 'organisationId' not in attrs
    ''', ENTRYPOINT=entrypoint, AIENT_PUBLISHABLE_KEY='test-only',
        OTEL_SERVICE_NAME='cream-test', OTEL_EXPORTER_OTLP_ENDPOINT='https://capture.invalid/',
        COMMIT_SHA='a' * 40, COMMIT_REF='main', AIENT_ENV='test',
        OTEL_EXPORTER_OTLP_COMPRESSION='none')
