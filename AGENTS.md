# Agents

We're developing a CRM tool called "Cream"; it is developed for use by
Functional Software, a recruitment company that also does consultant brokering.
In additional to tracking customers and leads, it also tracks candidates.

## Process

- Commit your work after you have finished a task.
- Run tests and verify that they all pass before committing.
- `uv` is used for local development. Environment variables are
  sourced from an `.env` file, but they should be picked up automatically. If
  not, you may need to invoke `uv` with `uv run --env-file .env`

## Testing

- Use test-driven development.
- Tests are written with pytest (+ pytest-django); run them with `uv run pytest`.
- Don't write tests for frontend functionality; prefer doing a one-off browser
  test instead to verify the implementation.

## Browser testing

- Start the local development server with `uv run manage.py runserver`. If it
  is already running, reuse it; if port 8000 is occupied, verify that the
  running site is Cream before proceeding.
- Confirm the site is running on localhost before logging in with the local
  development credentials `admin` / `admin`.
- Feel free to create and edit test data. Prefer editing data created during
  the current test, and avoid deleting existing data.
- Make a best-effort cleanup of test data. Only remove records known to have
  been created by the test.

## Tech stack

- Django
- uv
- Docker
- Postgres
- Bootstrap (vendored CSS/JS, no build step)

## Misc.

- `requirements.txt` is generated from `uv.lock` for the production Docker
  image (pip can't read uv.lock). After adding/removing/updating
  dependencies, regenerate it and commit both files:
  `uv export --no-dev --no-emit-project -o requirements.txt`
