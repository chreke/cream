# Deployment

## Overview

Cream runs on a single VPS as a two-container docker compose stack (app +
Postgres) behind the VPS's existing nginx, which terminates TLS via the
already-configured certbot. Deploys are intentionally low-tech: an
external script (maintained outside this repo) rsyncs the source tree to
the VPS and restarts the stack. This spec covers everything the *repo*
must provide for that to work, plus the documented nginx/first-boot steps.

Out of scope: backups (the VPS has a native backup solution), CI, image
registries, zero-downtime deploys, error alerting.

## Requirements

### Application image

- A `Dockerfile` builds the app image: dependencies installed with uv,
  gunicorn as the WSGI server.
- `collectstatic` runs at image build; whitenoise serves the result with
  hashed filenames and compression (manifest storage), so nginx needs no
  `/static/` location.
- The image contains no secrets and no `.env`.

### Compose stack

- A production compose file defines two services: the app and Postgres.
- Postgres uses the official image pinned to major version 17
  (ICU-enabled, as required by the `sv-SE-x-icu` collation on the name
  fields).
- Postgres data and `MEDIA_ROOT` (uploaded resumes) live on volumes/bind
  mounts that survive `compose down` and image rebuilds.
- **Media is never served by nginx or whitenoise** — resumes are
  auth-gated through Django (specs/010), so nginx must have no `/media/`
  location, and the media volume is only mounted into the app container.
- The app container binds to localhost only (nginx is the sole public
  entry).
- On start, the app container runs `migrate` (idempotent) before starting
  gunicorn — this is how deploys apply migrations.
- Restart policy brings the stack up after crashes and VPS reboots.

### Configuration

- All production config comes from an env file on the VPS (never in the
  repo, never in the image, never overwritten by deploys): `SECRET_KEY`,
  `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `POSTGRES_*`, and optional
  `DEBUG`.
- The hostname is configuration, not code: `ALLOWED_HOSTS` and
  `CSRF_TRUSTED_ORIGINS` come from the env file, and nothing in the repo
  (settings, compose, docs examples) hardcodes or assumes the real
  hostname — documentation uses a placeholder.
- Safe by default: `DEBUG` is **off** unless explicitly enabled; local
  dev turns it on in its `.env`. No hardcoded secret key in settings for
  production use.
- Since nginx terminates TLS: `SECURE_PROXY_SSL_HEADER`, secure
  session/CSRF cookies, and HSTS when not in debug.
- `manage.py check --deploy` passes cleanly with production env.
- The dev workflow (`uv run` + `.env`, tests, README instructions) keeps
  working unchanged.

### nginx (documented, not managed by the repo)

- The repo documents an example server block: `proxy_pass` to the app's
  localhost port, `Host`/`X-Forwarded-Proto` headers, and
  `client_max_body_size 25m` so resume uploads fit (nginx's 1 MB default
  is too small).
- TLS/certificates: one more certbot-managed subdomain on the existing
  setup; not this spec's job beyond the documented server block.

### Deploy contract (what the external script can rely on)

- rsync the repo tree to a directory on the VPS (excluding at least
  `.git`, `media/`, `.env`, caches).
- `docker compose -f <prod compose file> up -d --build` from that
  directory is the entire deploy: build, migrate, restart.
- First-time setup is documented in the README: create the env file (from
  a committed `.env.example`-style template), start the stack,
  `createsuperuser` inside the container.

### Documentation

- The README gets a Deployment section: prerequisites on the VPS (Docker
  + compose plugin, existing nginx/certbot), first-time setup (env file
  from the committed template, `docker compose -f <prod file> up -d
  --build`, `createsuperuser` in the container), how subsequent deploys
  work (rsync + compose up), how to run one-off management commands, and
  the example nginx server block (or a pointer to it).
- The existing dev-setup sections stay accurate and unchanged in
  behavior.

## Edge cases

- A deploy while a resume upload is in flight: acceptable (seconds of
  downtime; internal tool).
- Migrations that fail on start must leave the old DB state intact
  (Django migrations are transactional on Postgres) and keep the
  container restarting visibly rather than serving a broken app.
- `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` misconfiguration is surfaced by
  `check --deploy` before first deploy.
