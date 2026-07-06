# Lead Models

## Overview

Data model for Leads: the `Lead` model itself, its association to Candidates,
and Django Admin registration. No UI in this task — CRUD, detail page, and
pipeline come in later subtasks (see `TODO.md`). The pipeline mockup
(`specs/Sales Pipeline.png`) informed the attribute list; it becomes the
reference for the board subtask.

## Requirements

### Lead

A lead is a business opportunity with a Company, with the following
attributes (\* = required):

- **Name\*** — sorts with Swedish collation, like other name fields
- **Company\*** — deleting a company deletes its leads
- **Expected value** — money in SEK, no currency field; optional
- **Expected close date** — optional date (shown on pipeline cards in the
  mockup)
- **Contact** — a Contact belonging to the same company; optional. Deleting
  the contact keeps the lead (the field is cleared)
- **Assignee** — a User; optional. Deleting the user keeps the lead (the
  field is cleared)
- **Stage\*** — one of *Pågående* (in progress), *Offert* (quote),
  *Intervju* (interview), *Vunnen* (closed–won), *Förlorad* (closed–lost).
  New leads default to *Pågående*. How the board renders the two closed
  stages is decided in the pipeline subtask
- **Created at** — set automatically; used later to order cards within a
  pipeline column

### Candidates

A lead may have any number of associated Candidates (plain many-to-many, no
per-candidate state). Deleting a candidate or a lead just dissolves the
association; neither side is otherwise affected.

### Validation

- A lead's contact must belong to the lead's company.
- Expected value cannot be negative.

### Admin

Registered in Django Admin: list shows name, company, stage, expected value,
and assignee; filterable by stage and searchable by name/company name.

### Out of scope

- Lead comments (`LeadComment` arrives with the Comments subtask).
- All views and templates.
- Any changes to how candidates or companies behave.

## Notes

- In the mockup the site copy calls leads "affärer" ("Affär skapad",
  "2 affärer"); UI copy should follow that, but it's a concern for the CRUD
  subtask, not the model.
