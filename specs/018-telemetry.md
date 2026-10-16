# Aient telemetry

## Scope

Cream is a Python 3.13 / Django 5.2 application. Gunicorn imports
`cream.wsgi:application` in each worker (no `--preload`); `cream.asgi` is the
alternate bootstrap. Initialize standard OpenTelemetry there before Django loads
middleware, not from settings or AppConfig (which also run during builds and
migrations). Export batched OTLP/HTTP protobuf traces and Python warning/error
logs using an env-provided publishable key. SDK shutdown hooks flush on normal
worker exit. No collector credentials or organisation IDs belong in source.

Release metadata comes from `COMMIT_SHA`, `COMMIT_REF`, and `AIENT_ENV`.
Compose passes the deployed full SHA/branch into the Docker build and the image
retains them for runtime. The external rsync deployment must supply these values
from its source checkout, since `.git` is excluded from the image and deploy.

## Browser and source maps

There is no application browser bundle or JavaScript build: Django renders
templates and serves plain `static/js/*.js` and pre-vendored libraries from
`static/vendor`. Docker only runs `collectstatic`; there is no package manifest,
bundler, or CI build. Do not introduce a JS toolchain/browser SDK for this Python
service. Browser identity/export/persistence verification is not applicable.
Python ships source, not transpiled server output; source-map generation/upload
is not applicable. Existing vendor maps stay intact for manifest storage.

## Verification

Isolated subprocess tests capture real OTLP protobuf requests without a server or
live key. Exercise both bootstraps, repeated configuration, disabled capture,
full-SHA validation, actual Django request spans, correlated warning logs,
resource metadata, bearer auth, endpoint paths, and flush/shutdown. Run the full
pytest suite and the production `collectstatic` build after locked installation.
Live Aient delivery requires deployment configuration and cannot be verified
without a publishable ingest key.

Verified with Python 3.13, locked `uv sync`, the full pytest suite against a
disposable Postgres 17 database, `manage.py check --deploy`, Python compilation,
and `docker build` (including pip installation of the generated requirements and
production `collectstatic`). The published Django instrumentor's `asgi` extra is
required for ASGI spans and is included in the lock/export. No browser test or
live ingest request was performed. The external deployment script still needs
the per-deploy SHA/branch input and the VPS needs its runtime publishable key.
