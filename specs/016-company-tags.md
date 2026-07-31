# 016 — Company tags

Status: Done (2026-07-31)

Add reusable, user-defined tags to companies. Tags are intentionally generic:
they may describe a technology (`Python`, `.NET`), a commercial signal (`Het`),
or another useful grouping (`Partner`). The immediate use case is filtering the
company list by tech stack, but the data model and UI must not restrict tags to
technologies.

## Data model

- Add a `Tag` model with a single `name` field (maximum 100 characters).
- Tag names are trimmed and may not be blank.
- Names are unique case-insensitively, so `React`, `react`, and ` React ` refer
  to the same tag. Preserve the capitalization of the first saved name for
  display; names such as `.NET`, `C#`, and `Node.js` must not be lowercased.
- Tag names use the project's Swedish database collation and sort
  alphabetically by name.
- Add a blankable many-to-many relationship from `Company` to `Tag`, with a
  reverse relationship from tags to their companies.
- Register `Tag` in Django Admin. Renaming a tag there changes its display name
  for every associated company. Deleting a tag removes its company
  associations but never deletes a company.
- Removing the last company association does not delete the tag. Unused tags
  remain available for future use and may be cleaned up through Admin.

## Company create/edit form

- Add a field labelled `Taggar` to both company create and edit modals.
- Enhance the field with the already-vendored Tom Select. It is a multi-select
  that:
  - searches the existing tags;
  - allows creating a tag by typing its name;
  - shows each selected tag as a removable item; and
  - preselects all of the company's existing tags when editing.
- New tags are persisted when the valid company form is submitted; creating a
  tag does not require a separate request or management screen.
- The server performs trimming, case-insensitive matching, and deduplication.
  A differently-cased value matching an existing tag attaches the existing
  tag rather than creating another one.
- Saving an edited company replaces its tag associations with the submitted
  selection. Removing an item from the control only detaches that tag from the
  company.
- Without JavaScript, the field degrades to an ordinary multiple select of
  existing tags. Creating new tags without JavaScript is not required.

Tom Select provides the client-side tag-entry interaction (`create: true` and
the `remove_button` plugin). Django still owns validation and creation of the
shared `Tag` rows.

## Display

- Show a company's tags on the company list and company detail page.

## Company-list filtering

- Add a Tom Select multi-select tag filter alongside the existing search and
  assignee filters.
- The filter submits stable tag primary keys as repeated `tags` query
  parameters. Renaming a tag therefore does not break a saved filter URL.
- Multiple selected tags use **AND semantics**: a company must have every
  selected tag. Selecting `Python` and `AWS` excludes companies having only
  one of them.
- Make the AND behavior clear in the filter's label or help text.
- Tag filtering combines with name/location search and assignee filtering.
- Selected tags and all other filters survive sorting and pagination.
- Missing, malformed, or deleted tag ids in a URL are ignored.
- Free-text company search remains limited to company name and location; tag
  names are available only through the explicit tag filter.

## Tests

- Tag names are trimmed, reject blanks, and are unique case-insensitively while
  preserving display capitalization.
- Companies can have multiple tags and tags can belong to multiple companies.
- Creating and editing companies attaches existing tags, creates new tags, and
  removes omitted associations.
- Submitting a case variant of an existing tag reuses it.
- Company list and detail pages render their associated tags.
- Filtering by one tag works.
- Filtering by multiple tags uses AND semantics.
- Tag filtering combines with search and assignee filters.
- Tag parameters survive sort and pagination links; invalid ids are ignored.
- The form renders the Tom Select hooks and selected tags in edit mode.

## Manual verification

- In company create/edit, existing tags autocomplete and new tags can be
  created by typing; selected tags can be removed.
- Editing a company round-trips its selected tags correctly.
- Case and whitespace variants do not create duplicate tags.
- Selecting multiple list filters returns only companies carrying all of them.
- Search, assignee, tag filters, sorting, and pagination retain one another's
  query parameters.

## Out of scope

- Tag descriptions or categories.
- A dedicated tag-management page outside Django Admin.
- OR/any-tag filtering or an AND/OR toggle.
- Adding tag names to free-text company search.
- Tags on candidates, contacts, or leads.
- Workflow behavior attached to specific tags. For example, `Het` is only a
  label in this version; it does not trigger reminders or reports.
