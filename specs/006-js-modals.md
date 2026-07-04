# Spec 006: JS pop-up modals for create/edit/delete

Status: Done (2026-07-04)

Reworks the server-rendered modals from specs 004/005 into client-side
Bootstrap modals. The modal markup is embedded in the page that hosts it
and opened with Bootstrap's data attributes (`data-bs-toggle="modal"`).

## Scope (all modals)

- Company create (embedded in the list page)
- Company edit, company delete confirm, log contact, contact create,
  contact edit (one per contact card), contact delete confirm, comment
  delete confirm (all embedded in the company detail page)
- Comment editing stays inline (spec 005) — not a modal.

## Decisions

- **No custom JavaScript except auto-open on validation errors**: a
  one-line script (rendered only when a POST failed validation) opens the
  relevant modal on page load so errors and input are preserved. Bootstrap
  manages backdrops/dismissal; HTML5 attributes (required, type=url) catch
  most errors before the server does.
- **Form endpoints are POST-only; GET redirects** to the page hosting the
  modal (list for create, detail for the rest). No more GET-rendered modal
  pages; the six standalone modal templates are deleted.
- **Unique form field ids**: pages embed several forms, so each form gets
  an `auto_id` prefix (e.g. `contact-<pk>-%s`).
- **Switching modals** (edit -> delete confirm) uses Bootstrap's built-in
  toggle-between-modals behavior.
- Delete confirmations are now client-side modals; deletion still only
  happens on POST.

## Dropped

- Templates: company_form, company_confirm_delete, contact_form,
  contact_confirm_delete, log_contact, companycomment_confirm_delete
- The list-backdrop rendering machinery (CompanyModalMixin context)
