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

Create the database and apply migrations:

```sh
/opt/homebrew/opt/postgresql@15/bin/createdb cream
uv run python manage.py migrate
```

Create a user account so you can log in:

```sh
uv run python manage.py createsuperuser
```

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

Settings are read from environment variables. If you want local overrides,
put them in a `.env` file in the project root (git-ignored) and use uv's
built-in env-file support:

```sh
uv run --env-file .env python manage.py runserver
```

To avoid typing the flag every time, set `UV_ENV_FILE=.env` in your shell
profile and `uv run` will pick the file up automatically.

The defaults work for local development without any configuration:

| Variable            | Default     |
| ------------------- | ----------- |
| `POSTGRES_DB`       | `cream`     |
| `POSTGRES_USER`     | (OS user)   |
| `POSTGRES_PASSWORD` | (empty)     |
| `POSTGRES_HOST`     | `localhost` |
| `POSTGRES_PORT`     | `5432`      |
