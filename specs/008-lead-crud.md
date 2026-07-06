# Lead CRUD

## Overview

Create, edit, and delete leads, plus a lead detail page. The pipeline page
is the home for leads: it gets the "Ny affär" button now and the kanban
board later. UI copy calls a lead **"affär"**; code, URLs, and this document
keep saying *lead*.

## Requirements

### Creating

- The pipeline page has a "Ny affär" button opening a create modal.
- The modal's fields: name\*, company\* (dropdown of all companies),
  expected value, assignee. **No contact field** (set via edit later) and
  **no stage field** — new leads always start as *Pågående*.
- After creating, redirect to the new lead's detail page.

### Detail page

Shows all attributes: name, stage, company (linked to its detail page),
expected value formatted like the mockup ("100 000 kr", blank shown as "–"),
contact, and assignee. Comments and candidates arrive in later subtasks.

### Editing

- Edit/delete via modals on the detail page, per the UI conventions (delete
  button in the edit modal, confirmation dialog, flash-and-redirect on
  server-side validation errors).
- Editable: name, expected value, contact, assignee, stage.
- **Company is fixed** — shown in the modal but not changeable. Wrong
  company means delete and recreate.
- The contact dropdown only offers the lead's company's contacts (plus
  empty). Server-side, a contact from another company is rejected (already
  enforced by the model).

### Deleting

Delete confirms first, then redirects to the pipeline page.

### Defaults / details

- Expected value is a plain number input (whole SEK typical; decimals
  accepted since the field allows them).
- No default assignee (consistent with companies).
- The detail page header shows the stage as a badge.
- Until the board and the company-page lead list exist, the pipeline page
  stays otherwise empty; leads are reached via the post-create redirect
  (and the admin).

### Out of scope

- The success toast in the mockup ("Affär skapad") — the app currently has
  no success flashes; consider separately.
- Candidates, comments, company-page lead list, board, drag & drop.
