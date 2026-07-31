# CLAUDE

We're developing a CRM tool called "Cream"; it is developed for use by Functional
Software, a recruitment company that also does consultant brokering. In
additional to tracking customers and leads, it also tracks candidates. This
document describes the functional requirements for Cream.

## Requirements

All high-level functional requirements are documented in `REQUIREMENTS.md`. It is
important that this document be kept up to date.

## Process

- Work should be tracked in the `TODO.md` file. 
    - Any complex task should also be tracked as a "spec document", stored in
      `specs/`, and linked to from the `TODO.md` file. (Treat this as an issue
      tracker)
    - Feel free to track work and add tasks to `TODO.md` at will.
- Commit your work after you have finished a task.
- Run tests and verify that they all pass before committing.

## Testing

- Use test-driven development.
- Tests are written with pytest (+ pytest-django); run them with `uv run pytest`.

## Tech stack

- Django
- uv
- Docker
- Postgres
- Bootstrap (vendored CSS/JS, no build step)

## Misc.

- Django's `{# ... #}` template comments are single-line only: a multi-line
  `{# ... #}` is not parsed as a comment and leaks literally into the
  rendered HTML. Use `{% comment %}...{% endcomment %}` for anything longer
  than one line. (This is guarded by a test that scans rendered pages for
  `{#`.)

- Do *not* write memory files! If there's something you think we need to remember,
  please add it to this file instead.
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
