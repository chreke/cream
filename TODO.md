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
    - [ ] Resumes: file upload, authenticated serving
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
    - [ ] Comments (reuse the shared comment feed partial)
    - [ ] Company integration: company detail page lists its leads
    - [ ] Pipeline board: kanban view grouped by stage with per-stage sums
          of expected value (stage changes via the edit modal for now)
    - [ ] Drag & drop: move leads between stages on the board
- [ ] Deployment
- [x] Swedish collation: name sorting puts Å/Ä/Ö with A/A/O instead of after Z
      (fixed with `db_collation="sv-SE-x-icu"` on the name fields)
- [ ] Candidates on a lead: attach/detach candidates, flag status visible,
      maybe a comment on attach — picker UI needs design work, deferred
      ([spec](specs/009-lead-candidate-picker.md))

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
