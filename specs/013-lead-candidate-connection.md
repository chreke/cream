# Lead–Candidate Connection

Supersedes `specs/009-lead-candidate-picker.md` (deferred discussion; its
naive-widget rulings and challenges carry over).

## Overview

Leads and candidates are already linked by a plain M2M (`specs/007`). This
spec adds the UI on both ends, plus soft-deletion of leads so that the link
history survives:

1. Attach/detach candidates on the lead detail page, with a Tom Select
   autocomplete picker backed by server-side search.
2. An "Affärer" section on the candidate detail page linking back to the
   candidate's leads — with the company name prominent, so it's visible
   that a candidate has been sent to a given company before (e.g. to avoid
   re-sending a previously rejected candidate).
3. Leads are soft-deleted so those back-links never dangle.

Decisions carried over from the 009 discussion: the association stays a
**plain M2M** (no per-candidate status — lead + stage gives enough
information); **no comment on attach** (the lead's ordinary comment feed is
one scroll away); **no flag icons** in these sections.

## Requirements

### Candidate section on the lead detail page

- The lead detail page gets a candidate section listing attached
  candidates: name (linked to the candidate page), location and skills.
  Skills are truncated to at most 40 characters. No flag icons.
- Each row has a "Ta bort" button that detaches the candidate (POST).
  Detaching never deletes the candidate itself.
- Empty state text when no candidates are attached.

### Attaching candidates (Tom Select picker)

- The section contains a picker: a Tom Select single-select with
  **server-aided autocomplete** — typing queries the server (the existing
  ranked full-text candidate search) and shows the top matches.
- Each option shows name, location and skills, enough to tell namesakes
  apart; the selection submits the candidate **id**.
- Already-attached candidates don't appear in the results.
- Picking a candidate does not attach by itself: a "Lägg till" button
  submits the attach (POST).
- Attach is idempotent.
- The autocomplete endpoint returns JSON and requires login.
- Tom Select is vendored (CSS + JS, no build step), consistent with how
  Bootstrap is vendored.
- Graceful degradation is nice-to-have, not required: without JS the picker
  may be unusable, but the rest of the page must still work.

### Leads on the candidate detail page

- The candidate detail page gets an "Affärer" section listing every lead
  the candidate is attached to, including soft-deleted ones.
- Each row shows: **company name** (prominent — this is the "have we sent
  them here before?" signal), lead name (linked to the lead detail page),
  stage, and creation date.
- Soft-deleted leads are visibly marked (e.g. "borttagen") but still listed
  and linked.
- Empty state text when the candidate is on no leads.

### Soft-deleting leads

- Deleting a lead marks it deleted instead of removing the row. Existing
  delete UI keeps working, but performs a soft delete.
- Soft-deleted leads disappear from the pipeline board (and its per-stage
  sums) and any other lead listings.
- The lead detail page of a deleted lead stays reachable (so candidate-page
  links work): it shows a clear "deleted" banner with a **restore** button.
- A deleted lead otherwise behaves like any other: editing, commenting and
  attaching/detaching candidates all keep working — it's just hidden from
  the pipeline until restored.
- Restoring returns the lead to the pipeline in its current stage, with
  comments and candidate links intact.
- Hard deletion remains possible only via the Django admin.

### Pipeline board

- Each kanban card shows the lead's real candidate count (currently
  hardcoded to 0 from the mockup).

## Edge cases

- Two candidates with the same name: distinguished in the picker by
  location/skills; ids are what's submitted.
- Deleting a **candidate** still hard-deletes (unchanged); it silently
  disappears from any leads.
- Deleting a company still cascades to its leads, including soft-deleted
  ones. Accepted: deleting a company is rare and signals we don't intend to
  do business with them again, so losing that history is fine.
- Concurrent attach of the same candidate (double click): idempotent, no
  error, no duplicate rows.

## Out of scope

- Per-candidate status on the association (revisit if "lead stage +
  presence" proves too coarse).
- Comments as part of the attach flow.
- Soft-deleting anything other than leads.
