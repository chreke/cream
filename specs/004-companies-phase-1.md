# Spec 004: Companies, phase 1 — model, list, create/edit

Status: Done (2026-07-04)

Phase 1 of the Companies feature. Phase 2 (detail page, contacts,
log-contact, comments) is specced separately when we get there.

## Scope

- `Company` model with fields from REQUIREMENTS.md: name (required),
  location, industry, homepage, organization number, description
  (Markdown source, no rendering yet), assignee (User), last contacted.
- Companies list as a table: Name, Location, Industry, Assignee,
  Last contacted.
  - Free-text search on name + location.
  - Filter by assignee.
  - Sort by name (default, ascending) or last contacted.
  - Paginated, 50 per page.
- Create and edit forms. The list has a "Nytt företag" button linking to
  the create page. Table rows carry no edit/delete links — the edit page
  exists at its URL but gets its entry point (the detail page) in phase 2.
- Registered in the Django admin.

## Decisions

- **"Assignee" and "account manager" are the same field** — REQUIREMENTS.md
  normalized to "Assignee". Swedish UI label: "Ansvarig".
- **Sorting by last contacted puts never/least-recently contacted first**
  (nulls first, ascending) — the CRM use case is finding companies that
  need attention.
- **Create/edit happen in pop-over modals** (REQUIREMENTS.md "UI" section),
  rendered server-side with no JavaScript: the create/edit/delete URLs
  render the companies list with the modal already open on top. Validation
  errors re-render with the modal open.
- **Edit/delete have no entry points in the table** (per user). The edit
  modal contains a "Ta bort" button, which leads to a delete-confirmation
  modal (deletes on POST only). The edit modal's entry point arrives with
  the phase 2 detail page.
- **Swedish labels live on the form/templates**, not as model
  verbose_names — the admin and code stay English.
- Assignee is `on_delete=SET_NULL` — removing a user must not delete
  their companies.
- Markdown rendering (and the `markdown` dependency) deferred to phase 2,
  where the description is first displayed.

## Out of scope (phase 2)

- Company detail page
- Contacts
- "Log contact" flow (updates last_contacted, optional comment)
- Comments (built generically for reuse by candidates/leads)
