# Spec 017: Typed contact comments

Status: Planned

## Goal

Make a contact logged through the company detail page visibly different from
an ordinary user comment, while keeping both in the existing chronological
comment feed.

## Scope

- Add a `type` enum field to the abstract `BaseComment` model with two values:
  `Comment` and `Contact`.
- Default the field to `Comment`. Existing company, candidate, and lead
  comments are migrated as `Comment`; their original source cannot be inferred
  reliably.
- Comments submitted through ordinary comment forms are always `Comment`.
  Users do not select or edit the type manually.
- Logging contact always creates a `CompanyComment` with type `Contact`, even
  when the optional comment input is empty.
- A contact comment starts with `Kontaktad <timestamp>`, using the timestamp
  selected in the Logga kontakt form. Optional user-entered text follows that
  generated content, separated by a space.
- A `Contact` comment displays a phone icon in the shared comment feed. The
  icon has an accessible text alternative identifying the item as a contact.
- Editing a contact comment changes its content but preserves its type.

## Examples

With no user-entered text:

```text
Kontaktad 2026-08-07 09:24
```

With user-entered text:

```text
Kontaktad 2026-08-07 09:24 Ringde och bokade möte.
```

## Out of scope

- Retrospectively guessing which existing comments originated from the old
  Logga kontakt flow.
- Letting users change a comment's type.
- Additional contact channels or types such as meeting, email, or phone call.
