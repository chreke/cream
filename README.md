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
```

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

Settings are read from environment variables via `os.environ[]` — they are
**required**, and Django will refuse to start if any is missing. For local
development, put them in a `.env` file (git-ignored) and load it with uv's
built-in env-file support (`UV_ENV_FILE=.env` or `uv run --env-file .env`).

| Variable            | Purpose                                     |
| ------------------- | ------------------------------------------- |
| `POSTGRES_DB`       | Database name (`cream` locally)             |
| `POSTGRES_USER`     | Database user (your OS user for Homebrew)   |
| `POSTGRES_PASSWORD` | Database password (empty for local Homebrew)|
| `POSTGRES_HOST`     | Database host (`localhost` locally)         |
| `POSTGRES_PORT`     | Database port (`5432`)                      |
