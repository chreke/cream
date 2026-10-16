"""Opt-in OTLP/HTTP telemetry, initialized once per serving worker."""

import logging
import os
import re

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_configured = False
_logger_provider = None
_logging_handler = None


class _ExcludeTelemetryLogs(logging.Filter):
    def filter(self, record):
        # Export failures must remain on stderr, not enqueue further exports.
        if record.name == 'opentelemetry' or record.name.startswith('opentelemetry.'):
            return False
        # Django adds the entire request to error records. Do not serialize it
        # as a log attribute; leave the original record intact for console use.
        attributes = vars(record).copy()
        attributes.pop('request', None)
        return logging.makeLogRecord(attributes)


def configure_telemetry():
    """Call before Django constructs its middleware; never in the master process.

    The SDK owns batching and atexit flush/shutdown. Gunicorn must not use
    --preload: its normal worker-local WSGI import is the integration point.
    """
    global _configured, _logger_provider

    key = os.environ.get('AIENT_PUBLISHABLE_KEY')
    if _configured or not key or os.environ.get('OTEL_SDK_DISABLED', '').lower() == 'true':
        return

    commit = os.environ.get('COMMIT_SHA')
    if commit and not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('COMMIT_SHA must be a full 40-character lowercase Git SHA')
    branch = os.environ.get('COMMIT_REF')
    environment = os.environ.get('AIENT_ENV')
    attributes = {
        'service.name': os.environ.get('OTEL_SERVICE_NAME') or 'cream',
        'release.commit': commit,
        'release.branch': branch,
        'release.environment': environment,
        'deployment.commit_sha': commit,
        'deployment.commit_ref': branch,
        'deployment.environment': environment,
    }
    resource = Resource.create({name: value for name, value in attributes.items() if value})
    endpoint = (os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT') or 'https://ingest.aient.ai').rstrip('/')
    headers = {'Authorization': f'Bearer {key}'}

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=f'{endpoint}/v1/traces', headers=headers),
    ))
    trace.set_tracer_provider(tracer_provider)
    _logger_provider = LoggerProvider(resource=resource)
    _logger_provider.add_log_record_processor(BatchLogRecordProcessor(
        OTLPLogExporter(endpoint=f'{endpoint}/v1/logs', headers=headers),
    ))
    set_logger_provider(_logger_provider)
    DjangoInstrumentor().instrument(tracer_provider=tracer_provider)
    _configured = True


def configure_logging():
    """Attach after Django's logging configuration; preserve console logging."""
    global _logging_handler

    if _logger_provider is None or _logging_handler is not None:
        return
    handler = LoggingHandler(level=logging.WARNING, logger_provider=_logger_provider)
    handler.addFilter(_ExcludeTelemetryLogs())
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(logging.StreamHandler())
    root.addHandler(handler)
    # Django's development HTTP logger does not propagate to root.
    server_logger = logging.getLogger('django.server')
    if not server_logger.propagate:
        server_logger.addHandler(handler)
    _logging_handler = handler
