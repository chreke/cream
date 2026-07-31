# Agents

We're developing a CRM tool called "Cream"; it is developed for use by
Functional Software, a recruitment company that also does consultant brokering.
In additional to tracking customers and leads, it also tracks candidates.

## Requirements

All high-level functional requirements are documented in `REQUIREMENTS.md`. It is
important that this document be kept up to date.

## Process

- Work should be tracked in the `TODO.md` file. 
    - Any complex task should also be tracked as a "spec" Markdown document,
      stored in `specs/`, and linked to from the `TODO.md` file. (Treat this as
      an issue tracker)
    - Spec file names are snake case with a three-digit prefix, e.g.
      `001-initialize-django-project.md`
    - Feel free to track work and add tasks to `TODO.md` at will.
- Commit your work after you have finished a task.
- Run tests and verify that they all pass before committing.
- `uv` is used for local development. Important! Environment variables are
  sourced from an `.env` file, so you may need to run `uv` with `uv run
  --env-file .env`

## Testing

- Use test-driven development.
- Tests are written with pytest (+ pytest-django); run them with `uv run pytest`.

## Browser testing

- Start the local development server with `uv run manage.py runserver`. If it
  is already running, reuse it; if port 8000 is occupied, verify that the
  running site is Cream before proceeding.
- Confirm the site is running on localhost before logging in with the local
  development credentials `admin` / `admin`.
- Reload the page after code changes so the current implementation is being
  tested.
- Feel free to create and edit test data. Prefer editing data created during
  the current test, and avoid deleting existing data.
- When deletion itself must be tested, create a disposable record and delete
  only that record.
- Make a best-effort cleanup of test data. Only remove records known to have
  been created by the test; remove shared records such as tags only if they
  were created during the test and are no longer associated with anything.
- Verify user-visible outcomes rather than implementation hooks: resulting URL
  parameters, visible results, state persisted after reload, and computed
  styling when relevant. Do not substitute shallow template assertions for
  browser testing of interactive behavior.
- Check the browser console for warnings and errors after testing JavaScript.
- Test narrow layouts when the change affects responsive behavior.
- Report what was browser-tested and whether any test data could not be
  cleaned up.
- Browser testing complements pytest; it does not replace server-side model,
  form, view, and filtering tests.

## Tech stack

- Django
- uv
- Docker
- Postgres
- Bootstrap (vendored CSS/JS, no build step)

## Misc.

- Prefer low-JS, server-rendered UI: default to multi-page / form-POST flows;
  reach for JavaScript only when it's clearly worth it.
- Prefer class-based views (CBVs) over function-based views.
- Register models in the Django Admin by default.
- When vendoring minified CSS/JS, also vendor the `.map` files they
  reference: in production, ManifestStaticFilesStorage rewrites
  `sourceMappingURL` comments and collectstatic *fails* if the map file
  is missing.
- `requirements.txt` is generated from `uv.lock` for the production Docker
  image (pip can't read uv.lock). After adding/removing/updating
  dependencies, regenerate it and commit both files:
  `uv export --no-dev --no-emit-project -o requirements.txt`
