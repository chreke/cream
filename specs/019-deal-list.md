# Deal List ("Affärer")

## Overview

A table view of all deals (leads), mainly to answer "which deals did we win
during a given period?" and to find soft-deleted deals again. To support
this, leads get a "won date" (`closed_at`).

"Closed" and "Vunnen" (`Lead.Stage.WON`) are synonymous here; "Förlorad"
deals are not considered closed and never have a won date.

Soft deletion already exists (`specs/013`); this spec only makes deleted
deals listable.

## Requirements

### Won date (`Lead.closed_at`)

- A nullable date ("Vunnen den"). Only Vunnen deals may have one; this is
  enforced by a database check constraint, so a form submission that sets a
  won date on a deal that isn't Vunnen fails with a validation error.
- When a deal's stage changes *to* Vunnen (edit modal, pipeline drag & drop
  or creation) and no won date is given, it is set to today's local date.
- When a deal's stage changes *away from* Vunnen, the won date is cleared.
  If it is won again later, it gets a new date.
- The won date is editable in the lead edit modal. The input is only
  enabled while the stage select is set to Vunnen (client-side guard).
  It may be left empty on a Vunnen deal.
- Existing Vunnen deals are not backfilled; their won date is empty until
  edited.
- The won date is shown on the lead detail page.

### Deal list page

- New sidebar tab "Affärer" (`/leads/`), between "Kandidater" and
  "Pipeline".
- Table columns: Titel (linked to the lead detail page), Företag (linked
  to the company), Status (stage) and Vunnen den. Column widths are fixed,
  so they don't shift as filtering changes the rows; narrow screens scroll
  the table horizontally. Soft-deleted deals are greyed out.
- Filters (submit automatically on change):
  - Status: "Alla statusar" or a single stage.
  - "Visa borttagna" checkbox: deleted deals are hidden by default.
- Sorting by title (default, ascending) or won date; both can be reversed
  by clicking the active column header. Won-date sort puts the most
  recently won first, deals without a won date last.
- Header shows the number of matching deals; "Återställ" resets filters
  and sorting. Paginated at 50 rows, like the other lists.

Out of scope: date-range filtering (there are few enough deals that sorting
is sufficient for now).
