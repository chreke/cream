# DESIGN

This is a CRM tool called "Cream"; it is developed for use by Functional
Software, a recruitment company that also does consultant brokering. In
additional to tracking customers and leads, it also tracks candidates. This
document describes the functional requirements for Cream.

## General

- The site copy should be in Swedish.
- Prefer tables for rendering list views
- All sortable text fields must use Swedish collation (å/ä/ö sort after z),

## UI

- Editing and creating objects should be done in pop-over modals (see
  `specs/Modal.png`) rather than on separate pages.
- When editing, the modal should include a delete button. Deleting should
  always trigger a confirmation dialog.
- A successful edit should redirect to the object that was edited (e.g. the
  detail page it lives on).
- Each comment has an anchor link; after adding a comment, redirect to the
  new comment's anchor so it is scrolled into view. Comments are edited in a
  modal, like other objects.

## Users

The system should support multiple users. There is no split between different
User "roles"; all users have all privileges by default.

Users have the following information:

- Username
- Email address
- Password (recorded as a hash in the database)

## Companies

A Company has the following information:

- Name\*
- Location (e.g. Stockholm, Sweden)
- Industry
- Homepage
- Organization number
- Description (Markdown)
- Assignee (User)
- Last contacted (timestamp)

Required attributes are marked with an "\*"

A User can log that a Company was contacted; this updates the "Last contacted"
timestamp to the current time. The User may also leave a Comment as part of
logging a contact.

It should be possible to create, edit and delete companies.

### Companies List

It should be possible to display a list of all Companies. The following attributes
should be displayed in the list:

- Name
- Location
- Industry
- Assignee (User)
- Last contacted

It should be possible to sort the list by one of:

- Name
- Last contacted

It should be possible to filter Companies using free-text search. The
free-text search should target the Name and Location fields.

It should be possible to filter Companies by Assignee.

### Contacts

A Company may have one or more contacts. Contacts are displayed as cards on
the company detail page (an exception to the lists-as-tables rule). Each
contact has the following info:

- Name\*
- Role
- LinkedIn URL
- Email
- Phone number

Required attributes are marked with an "\*"

It should be possible to create, edit and delete contacts.

### Comments

Users can add comments to Companies. See the "Comments" section below.

## Candidates

A candidate has the following attributes:

- Name\*
- Location
- Email
- Phone number
- LinkedIn
- Description (Markdown)
- Flagged by (references the User that flagged the candidate)
- Flag reason (text)
- Skills (a comma-separated list of skills)
- Kind (Freelancer, Employee, Both)\*
- Location (e.g. "Stockholm, Sweden")
- Description (Markdown)

It should be possible to create, edit and delete candidates. After creating
a candidate, the user is redirected to the new candidate's detail page.

### Candidate Detail Page

Each candidate has a detail page showing all of the candidate's attributes:

- Email and phone number are rendered as clickable `mailto:`/`tel:` links,
  and LinkedIn as an icon linking to the profile.
- Skills are rendered as badges.
- The description is rendered as Markdown.

Editing and deleting the candidate is done from the detail page (in modals,
as per the UI section). The candidate's comments, flag status and resumes
(see below) also live on the detail page.

### Candidate Flagging

It should be possible to "flag" a candidate, which indicates that one needs
to take special consideration with this candidate, and that they might not
be appropriate for certain positions. When flagging a candidate, the User
may input an optional text that describes the reason for flagging the candidate.

Flags can be removed, and the reason for flagging may be edited. If a candidate
has their flag removed, the reason text is also deleted.

If a candidate is flagged, this should be made clear in all contexts where
the candidate appears.

### Resumes

It should be possible to upload one or more resumes for a given candidate. A
resume is an arbitrary document, e.g. a PDF or a Word document. It should be
possible to delete uploaded resumes.

### Candidates List

It should be possible to view a list of all candidates. The list should display
the following attributes:

- Name
- Location
- Kind
- LinkedIn URL (as a LinkedIn icon with a hyperlink)
- Skills (truncated if too long)

It should be possible to filter candidates using free-text search. The
free-text search should target the Name, Location and Skills fields.
Search matches whole words (all words in the query must match) and results
are ranked by relevance. See `specs/006-candidate-search.md` for details.

You should also be able to filter candidates based on their Kind. Note that you
should only be able to filter by "Freelancer" or "Employee"; candidates that
have "Both" should always be displayed.

### Comments

Users can add comments to candidates. See the "Comments" section below.

## Leads

A lead is a business opportunity with a Company. Each lead has the following
attributes:

- Name\*
- Company\*
- Expected value (money)
- Contact (Contact from the Company)
- Assignee (User)
- Stage (one of "In progress", "Quote", "Interview", "Closed")

Each lead may also have multiple associated Candidates.

It should be possible to create, edit and delete leads.

### Lead Pipeline

It should be possible to view a pipeline of leads, as a Kanban-board like
view where a Lead can be drag & dropped to different stages.

Each stage in the lead pipeline should also display a sum of the Expected
value of the leads in that stage.

### Comments

Users can add comments to Leads. See the "Comments" section below.

## Comments

Comments can be made on both Companies, Leads and Candidates.

A comment has the following attributes:

- Content (Markdown)
- User (who made the comment)
- Created at (timestamp)
- Edited at (timestamp)
- Last edited by (User)

Comments can be created, updated and deleted. A User can delete / edit comments
made by other users.

When displaying a comments, it should show who they were made / edited by.
