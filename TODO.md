# TODO

- [x] Initialize Django project ([spec](specs/001-initialize-django-project.md))
- [x] Create base template ([spec](specs/002-base-template.md))
- [x] Auth ([spec](specs/003-auth.md))
- [x] Companies 
    - [x] Model, list, create/edit ([spec](specs/004-companies-phase-1.md))
    - [x] Detail page, contacts, log contact, comments ([spec](specs/005-companies-phase-2.md))
- [ ] Candidates
    - [x] Models: Candidate model + admin
    - [x] List view: table, kind filter
    - [x] Search: full-text search ranked by relevance ([spec](specs/006-candidate-search.md))
    - [x] CRUD: detail page, create/edit/delete modals
    - [x] Comments
    - [x] Flagging
    - [x] Resumes: file upload, authenticated serving
          ([spec](specs/010-candidate-resumes.md))
- [x] Location inputs (companies + candidates) should autocomplete against
      existing values (via `<datalist>`; upgrade to Tom Select if the native
      UX proves too bare)
- [x] Editing a list item (e.g. a contact or comment) should redirect to an
      anchor link so the edited item is scrolled into view
- [x] Template comments leaking into rendered HTML: fixed, noted in
      CLAUDE.md, and guarded by a test
- [ ] Leads
    - [x] Models: Lead model + lead–candidate association + admin
          ([spec](specs/007-lead-models.md))
    - [x] CRUD: create/edit/delete modals, detail page
          ([spec](specs/008-lead-crud.md))
    - [x] Comments (reuse the shared comment feed partial)
    - [x] Pipeline board: kanban view grouped by stage with per-stage sums
          of expected value (stage changes via the edit modal for now)
          ([spec](specs/011-pipeline-board.md))
    - [x] Drag & drop: move leads between stages on the board
          ([spec](specs/012-pipeline-drag-drop.md))
- [ ] Deployment
- [x] Swedish collation: name sorting puts Å/Ä/Ö with A/A/O instead of after Z
      (fixed with `db_collation="sv-SE-x-icu"` on the name fields)
- [ ] Lead–candidate connection: Tom Select picker on the lead page,
      leads listed on the candidate page (company name prominent),
      soft-delete leads, real candidate counts on pipeline cards
      ([spec](specs/013-lead-candidate-connection.md); supersedes
      [009](specs/009-lead-candidate-picker.md))
- [ ] Truncate long skills lists in candidate rows (e.g. on the lead
      page's candidate section) — kept out of specs/013 on purpose
- [ ] Replace the current `<datalist>` usages (location inputs on
      companies + candidates) with Tom Select, once it's vendored for
      the lead–candidate picker (specs/013)
- [ ] Transfer data from Candide

## Verify manually

- [ ] Deleting companies
- [ ] Deleting candidates
- [ ] Deleting comments
- [ ] Edit comment redirects to the correct comment id in the URL
- [ ] Editing companies
- [ ] Flagging candidates
- [ ] Editing flags
- [ ] Unflagging candidates
- [ ] Creating leads ("Ny affär" on the pipeline page)
- [ ] Editing leads (contact dropdown only shows the lead's company's
      contacts; company not editable)
- [ ] Deleting leads
- [ ] Uploading a resume to a candidate
- [ ] Downloading a resume (and that /media/... URLs are *not* served)
- [ ] Deleting a resume (file disappears from `media/`)
- [ ] Pipeline board: columns look right, cards clickable, sums correct,
      horizontal scroll on narrow windows
- [ ] Drag & drop: card moves persist across reload, header sums update,
      dropping in the same column is a no-op, works on touch,
      card still clickable after a drag
