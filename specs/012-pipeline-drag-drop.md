# 012 — Pipeline drag & drop

Move leads between stages by dragging cards on the pipeline board
(specs/011). Decisions from design discussion 2026-07-07:

- **SortableJS, vendored** (`static/vendor/sortable.min.js`, MIT), like
  Bootstrap: no build step, and unlike hand-rolled HTML5 DnD it works on
  touch devices. This is the project's "JS only when clearly worth it"
  exception — the feature *is* the interaction.
- **No within-column reordering.** Dropping a card anywhere in a column
  changes the lead's stage, nothing else; the column re-sorts by name on
  the next render. No position field. (This also makes failure recovery
  trivial: on error, append the card back to its source column — order
  doesn't matter.)
- **Optimistic UI + sum patching.** The drop moves the card immediately;
  the client then POSTs the stage change, and the server responds with
  freshly formatted "N · X kr" summary strings for all columns, which the
  client writes into the column headers. No page reload.
- **The edit modal remains** the keyboard-/screen-reader-accessible way to
  change stage.

## Endpoint

`POST /leads/<pk>/stage/` (name `lead-stage`), form-encoded `stage=<value>`.

- Valid stage: save, return `200` JSON
  `{"summaries": {"in_progress": "2 · 200 000 kr", ...}}` (every stage,
  formatted server-side with the `sek` filter so Swedish number formatting
  lives in one place).
- Missing/unknown stage: `400` JSON with an error message; lead unchanged.
- Auth: `LoginRequiredMiddleware`, like everything else. CSRF applies;
  the client sends the token from the page's logout form.

## Client (`static/js/pipeline.js`)

- One `Sortable` per column body (`group: "pipeline"`), loaded via a new
  `{% block scripts %}` in `base.html`.
- Column bodies (the drop targets) carry `data-stage`; cards carry
  `data-stage-url` (their own endpoint URL, so the JS never builds URLs);
  header summaries carry `data-stage-summary="<stage>"`.
- `onAdd`: POST the move; on success update every summary element; on any
  failure (network, non-200, non-JSON) move the card back to the source
  column and alert via a flash-style message.
- Empty columns keep a `min-height` drop area.

## Tests

- Endpoint: valid move updates the lead and returns summaries reflecting
  it (both affected columns); unknown and missing stage → 400 and no
  change; anonymous POST redirects to login.
- Page: pipeline template includes sortable.min.js + pipeline.js and the
  `data-stage`/`data-lead-id`/`data-stage-summary` hooks.

The drag interaction itself is exercised manually (TODO's verify list).
