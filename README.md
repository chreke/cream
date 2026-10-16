# Cream

Cream is a CRM tool for Functional Software, tracking customers, leads and
candidates. See `REQUIREMENTS.md` for functional requirements.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — manages Python and dependencies
- PostgreSQL 14 or later, running locally

On macOS with Homebrew's keg-only `postgresql@15`, the client binaries are
not on your PATH; either add `/opt/homebrew/opt/postgresql@15/bin` to your
PATH or use the full path as shown below.

## First-time setup

Configuration is read from **required** environment variables (see
Configuration below). Create a `.env` file in the project root:

```sh
POSTGRES_DB=cream
POSTGRES_USER=<your macOS username>
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DEBUG=1
```

(`.env.example` in the repo root is a commented template for this file.)

Then set `UV_ENV_FILE=.env` in your shell profile so every `uv run` loads
it automatically. (Alternatively, pass `--env-file .env` to each `uv run`
command below.)

Create the database and apply migrations:

```sh
/opt/homebrew/opt/postgresql@15/bin/createdb cream
uv run python manage.py migrate
```

Create a user account so you can log in:

```sh
uv run python manage.py createsuperuser
```

Additional user accounts are created (and passwords reset) by a superuser
in the Django admin at `/admin/`; there is no self-service signup.

Dependencies are installed automatically by `uv run` on first use.

## Starting the app

```sh
uv run python manage.py runserver
```

The app is served at <http://127.0.0.1:8000/>.

## Running migrations

After pulling changes (or changing models yourself):

```sh
uv run python manage.py makemigrations  # only when models have changed
uv run python manage.py migrate
```

## Running tests

```sh
uv run pytest
```

## Configuration

Settings are read from environment variables. For local development, put
them in a `.env` file (git-ignored) and load it with uv's built-in
env-file support (`UV_ENV_FILE=.env` or `uv run --env-file .env`). See
`.env.example` for a commented template.

| Variable              | Purpose                                        |
| --------------------- | ---------------------------------------------- |
| `POSTGRES_DB`         | Database name (`cream` locally). Required.     |
| `POSTGRES_USER`       | Database user (your OS user for Homebrew). Required. |
| `POSTGRES_PASSWORD`   | Database password (empty for local Homebrew). Required. |
| `POSTGRES_HOST`       | Database host (`localhost` locally). Required. |
| `POSTGRES_PORT`       | Database port (`5432`). Required.              |
| `DEBUG`               | `1` enables debug mode. Set it in dev; leave unset in production. |
| `SECRET_KEY`          | Django secret key. Required in production (when `DEBUG` is unset). |
| `ALLOWED_HOSTS`       | Comma-separated hostnames. Required in production. |
| `CSRF_TRUSTED_ORIGINS`| Comma-separated origins with scheme (`https://…`). Required in production. |
| `PORT`                | Host port the app is published on behind nginx (production compose only, default `8000`). |
| `AIENT_PUBLISHABLE_KEY` | Publishable Aient ingest key. Empty/unset disables telemetry. Runtime only. |
| `OTEL_SERVICE_NAME` | Telemetry service name (default `cream`). |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP/HTTP base URL (default `https://ingest.aient.ai`; no `/v1/traces` suffix). |
| `AIENT_ENV` | Deployment environment slug, e.g. `prod` (not an environment ID). |
| `COMMIT_SHA` | Full 40-character lowercase Git SHA of the deployed source; required by production compose. |
| `COMMIT_REF` | Branch of the deployed source. |
| `OTEL_SDK_DISABLED` | `true` disables telemetry even with a key configured. |

### Aient / OpenTelemetry

Set the publishable ingest key in the VPS's `.env`, not in the Docker build.
WSGI/ASGI bootstraps initialize the standard Python SDK before Django builds
middleware, exporting batched request spans to `/v1/traces` and warning/error
Python logs to `/v1/logs` with bearer auth. Logs emitted inside a request carry
its trace/span IDs. Existing console logging is preserved. Resource attributes
include both `release.*` and `deployment.*` commit, branch, and environment.
Without a key, development, tests, migrations and `collectstatic` do not export.

Keep Gunicorn's existing **non-preloaded** worker model: do not add `--preload`
or initialize the SDK in the master. Normal worker termination invokes SDK
flush/shutdown hooks; forced kills cannot flush. Console-only loggers that do
not propagate to root (other than `django.server`) are not exported. Avoid
sensitive data in log messages or URL query strings; HTTP headers and bodies
are not explicitly captured by this integration.

No browser SDK or source-map upload is added: this server-rendered Python app
has no application JS bundle or transpiled server build. `collectstatic` copies
plain JS and vendored assets, retaining their existing maps. Browser identity
and persistence tests therefore do not apply. See [telemetry spec](specs/018-telemetry.md).

Bounded offline exporter verification (no server or live key):

```sh
uv run --locked pytest cream/test_telemetry.py
```

Live Aient ingestion still needs the deployed key and must be verified after
deployment; offline capture tests do not prove collector delivery.

## Deployment

Cream deploys to a single VPS as a docker compose stack — the app (gunicorn,
with whitenoise serving static files) plus Postgres 17 — behind the host's
existing nginx, which terminates TLS. See `specs/014-deployment.md` for the
full picture. Uploaded resumes live in the `data/media` bind mount and are
served through Django's authenticated views, **never** by nginx.

The compose file uses the default name (`docker-compose.yml`) so bare
`docker compose` commands work on the server — but that also means running
`docker compose up` in a local checkout starts the production stack, so
don't do that by accident. Local development is not containerized.

### Prerequisites on the server

- Docker with the compose plugin
- nginx with certbot already set up (Cream is one more server block)

### First-time setup

In the deploy directory on the server:

1. Copy `.env.example` to `.env` and fill in the production values
   (`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `POSTGRES_*`;
   leave `DEBUG` unset). Set `COMMIT_SHA` and `COMMIT_REF` to the source
   checkout's `git rev-parse HEAD` and `git branch --show-current`, respectively.
   Add `AIENT_PUBLISHABLE_KEY` to enable capture and set `AIENT_ENV` to the
   deployment's slug (the template uses `prod`).
2. Start the stack:

   ```sh
   docker compose up -d --build
   ```

3. Create the first user account:

   ```sh
   docker compose exec web python manage.py createsuperuser
   ```

4. Add an nginx server block (adjust the hostname; certbot manages the
   TLS parts):

   ```nginx
   server {
       server_name cream.example.com;

       # 25m fits resume uploads; nginx's default 1m does not.
       client_max_body_size 25m;

       location / {
           # Must match PORT in the deploy directory's .env (default 8000).
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Deploying a new version

rsync the repo tree to the deploy directory — excluding at least `.git/`,
`.env`, `data/` and caches — then rebuild. The external deployment script must
resolve `git rev-parse HEAD` (full SHA) and `git branch --show-current` **in the
source checkout** and update `COMMIT_SHA` / `COMMIT_REF` in the deploy `.env` on
every deploy, or export those same values in the remote compose environment:

```sh
docker compose up -d --build
```

Compose passes these public values to the Docker build and runtime; Docker
validates a supplied SHA and bakes it into the image. Since the external rsync
script is not in this repo, wiring that per-deploy input is a manual step.
Never derive the release from a short SHA or the VPS's stale/missing `.git`.

The image installs dependencies with pip from `requirements.txt`, which is
**generated** from `uv.lock` — after changing dependencies, regenerate it
and commit both:

```sh
uv export --no-dev --no-emit-project -o requirements.txt
```

Migrations run automatically when the app container starts. The Postgres
data and uploaded resumes live in `data/` inside the deploy directory
(bind mounts: `data/postgres`, `data/media`) and survive rebuilds; keeping
them there puts all state where the VPS's native backup solution sees it.
Deploy rsyncs and the app image must exclude `data/`.

### One-off management commands

```sh
docker compose exec web python manage.py <command>
```
