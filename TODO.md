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
    - [ ] Comments
    - [ ] Flagging
    - [ ] Resumes: file upload, authenticated serving
- [x] Location inputs (companies + candidates) should autocomplete against
      existing values (via `<datalist>`; upgrade to Tom Select if the native
      UX proves too bare)
- [ ] Leads
- [ ] Deployment
- [x] Swedish collation: name sorting puts Å/Ä/Ö with A/A/O instead of after Z
      (fixed with `db_collation="sv-SE-x-icu"` on the name fields)
