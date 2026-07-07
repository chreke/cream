# 011 — Pipeline board

Turn the pipeline page into a kanban-style board: one column per stage,
lead cards, per-stage sums. Reference mockup: `specs/Sales Pipeline.png`.
No drag & drop yet (separate TODO item); stage changes go through the
lead's edit modal.

Decisions (from design discussion 2026-07-07):

- **All five stages** get a column — Pågående, Offert, Intervju, Vunnen,
  Förlorad — even though the mockup shows four. Closed deals stay visible.
- **No date on cards.** The mockup's "1 aug. 2026" is an expected close
  date, a field the Lead model doesn't have. Not added now.
- **Cards show**: lead name (links to the detail page), company name, and
  expected value (`sek` filter). No candidate count, no assignee.
- **Creating stays as-is**: the single "Ny affär" header button; new leads
  land in Pågående. No per-column add buttons.

## Layout

- A horizontally scrollable flex row (`overflow-x-auto`, no wrapping) with
  five equal-width columns, so the board works on narrow screens without
  squeezing the cards.
- Column header: stage label plus "N · X kr" (count · summed expected
  value, mockup-style). Sum treats missing expected values as 0.
- Each column has `id="stage-<value>"` (e.g. `stage-quote`) — used by
  tests and handy as anchors.
- Cards within a column are ordered by name (model default). An empty
  column shows nothing but its header ("0 · 0 kr").

## View

`PipelineView` groups leads in Python from a single
`select_related("company")` query and builds a `columns` list of
`{stage, label, leads, total}` dicts. No JS.

## Tests

- All five column headers render.
- A lead's card appears in its own stage's column segment and not in
  others; card shows company name and value and links to the detail page.
- Per-stage header shows count and sum (two leads à 100 000 → "2 ·
  200 000 kr"); empty stages show "0 · 0 kr"; leads without a value count
  but add nothing.
