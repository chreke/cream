# Spec 001: Initialize Django project

Status: Done (2026-07-04)

## Decisions

- **Django 5.2 LTS** (supported until April 2028). Nothing in the requirements
  needs 6.x; if template partials become desirable, use the
  `django-template-partials` package instead of upgrading.
- **Local development without Docker.** Postgres runs natively via Homebrew
  (`postgresql@15`, keg-only — binaries at `/opt/homebrew/opt/postgresql@15/bin`).
  Docker is reserved for deployment.
- **Single Django app: `crm`.** All domain models (companies, candidates,
  leads, comments) live in one app; the domains are too interlinked to be
  worth splitting at MVP scale.
- **Custom user model** (`crm.User`, extends `AbstractUser`) from day one,
  per Django's own recommendation — switching later is very painful.
- **Database settings via environment variables** (`POSTGRES_DB`,
  `POSTGRES_USER`, etc.) with defaults that work for local dev: database
  `cream`, OS-user auth on localhost:5432.
- **Locale:** `LANGUAGE_CODE = 'en-us'`, `TIME_ZONE = 'Europe/Stockholm'`.
  Django's own locale (admin, framework messages, date formats) is English;
  the Swedish-copy requirement applies only to user-facing text we write
  ourselves in templates.

## Out of scope (later tasks)

- Base template with vendored Bootstrap
- Dockerfile / deployment setup
- Production settings hardening (SECRET_KEY from env, DEBUG off, etc.)
