# Spec 005: Companies, phase 2 — detail, contacts, log contact, comments

Status: Done (2026-07-04)

## Scope

- Company detail page, reached by clicking the company name in the list
  table (name is the only link; edit/delete stay off the table).
- Detail shows all company fields; description rendered as Markdown.
- Detail page header has "Redigera" and "Ta bort" buttons alongside
  "Logga kontakt". Delete goes straight to the confirmation modal.
- Contacts: listed on the detail page; created/edited in modals per the
  UI rule. Contact name links to its edit modal. Deleting goes through a
  confirmation modal.
- "Logga kontakt": button on the detail page opens a modal with an
  editable date/time field that defaults to the current Stockholm-local time,
  plus an optional comment field. Future timestamps are rejected. Submitting
  sets `last_contacted` to the selected timestamp and, if a comment was
  written, adds it to the company's comment feed.
- Comments on companies: feed on the detail page (newest first), with
  inline forms (not modals): new-comment textarea above the feed; editing
  swaps the comment for an inline form. Deleting a comment
  goes through a confirmation modal (the "always confirm deletion" rule).
  Any user may edit/delete any comment (per REQUIREMENTS.md); edits stamp
  `edited_at` and `last_edited_by`, shown in the feed.

## Decisions

- **One comment model per target** (user's choice): shared fields live in
  an abstract `BaseComment` (content, user, created_at, edited_at,
  last_edited_by); `CompanyComment` adds the company FK. Candidate/Lead
  comments will follow the same pattern.
- **Markdown via the `markdown` package**, with raw HTML escaped *before*
  rendering (XSS-safe, no sanitizer dependency). Known cost: `>`
  blockquote syntax doesn't survive escaping — acceptable.
  Implemented as a `|markdown` template filter.
- **Modal backdrops**: contact/log-contact/comment-delete modals render
  on top of the company detail page (same server-rendered pattern as
  spec 004).
- **After editing a company, you land on its detail page** (create still
  lands on the list; delete lands on the list).
- Comment author/editor FKs are `SET_NULL` — deleting a user keeps the
  comments.
- Contacts have no dedicated list/detail; they exist only on the company
  detail page. `on_delete=CASCADE` from company.

## Out of scope

- Comments on candidates/leads (their own tasks; they reuse BaseComment)
- Any changes to the companies list beyond linking the name
