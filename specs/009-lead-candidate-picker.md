# Lead Candidate Picker

## Status

**Deferred.** We started designing this and parked it; this document
captures the discussion so far. Nothing here is decided except that the
naive options are ruled out.

## Overview

A lead may have any number of associated candidates (M2M added in
`specs/007-lead-models.md`). This task is the UI for attaching and
detaching them, presumably from the lead detail page. Flagged candidates
must be recognizable wherever they appear — including in the picker and in
the lead's candidate list.

## Challenges

1. **The candidate list can be quite long** (thousands). Any widget that
   renders every candidate into the page — a plain `<select>` or a
   `<datalist>` — doesn't scale, in UX or page weight.
2. **Candidates may share names.** A `<datalist>` submits a string, not an
   id, so two "Erik Ek"s are indistinguishable server-side. Whatever picker
   we build must submit candidate *ids* and show enough context (location,
   skills, ...) to tell namesakes apart when choosing.
3. **It might be good to let the user leave a comment when attaching a
   candidate** (e.g. why this candidate fits). Open questions: does the
   comment go in the lead's comment feed, or does it belong to the
   lead–candidate association itself? The latter would reopen the plain-M2M
   decision from specs/007 (an association note needs a through-model).

## Options discussed

- **Plain `<select>`** — ruled out (challenge 1).
- **`<datalist>` autocomplete** (like the location inputs) — ruled out
  (challenges 1 and 2; locations get away with it because distinct values
  number in the dozens and uniqueness doesn't matter there).
- **Search-then-add, fully server-rendered** — a search box in the lead
  page's candidate section; submitting GETs the same page with the top ~10
  matches from the existing ranked full-text candidate search, each row
  showing name, flag icon, and skills with an "Lägg till" button that POSTs
  the attach (by id — solves challenge 2). No JS; wants to live inline on
  the page rather than in a modal (a modal doesn't survive the GET).
  *This was the working recommendation.*
- **Attach from the candidate's page instead** — "Lägg till i affär" with a
  select of open leads (a short list). Cheap complement, but the workflow
  likely starts from the lead.
- **Tom Select with remote search** — best UX, but the first real JS
  dependency plus a JSON search endpoint. Sanctioned by the TODO note that
  Tom Select is the upgrade path if native widgets prove too bare; the
  fallback if search-then-add feels clunky.

## Out of scope until resumed

The lead detail page doesn't show candidates at all yet; the pipeline-card
candidate count (mockup) will simply be 0 until this lands.
