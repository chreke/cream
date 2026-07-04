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

Use test-driven development.

## Tech stack

- Django
- uv
- Docker
- Postgres
- Bootstrap (vendored CSS/JS, no build step)

## Misc.

- Do *not* write memory files! If there's something you think we need to remember,
  please add it to this file instead.
- Prefer low-JS, server-rendered UI: default to multi-page / form-POST flows;
  reach for JavaScript only when it's clearly worth it.
- Prefer capabilities built into the existing stack (uv, Django, Postgres) over
  adding new dependencies (e.g. `uv run --env-file` instead of python-dotenv).
