# Agent README

Cream is our internal CRM and candidate tracker at https://cream.snork.dev. The UI is in Swedish. Work in it through the built-in browser (the browser pane in the desktop app).

## Signing in

Use a dedicated agent account, so agent actions are traceable separately from humans. The human operator will help you log in; you should not have access to the password. If a page redirects to /login/, open the login page in the browser pane and ask the user to sign in there with the agent account, then continue.

## Where things are

| What | Where |
|---|---| 
| Candidate list | /candidates/ (50 per page, ?page=N) | 
| Search by name | /candidates/?q=<name> | 
| Filter | location and kind query params (kind: freelancer, employee, both) | 
| Candidate profile | /candidates/<id>/ | 
| Other sections | /companies/ (Företag), /pipeline/ (Pipeline) |

Prefer get_page_text / read_page (or a short javascript_tool read of the DOM) over screenshots.

## Fields

| Label | Form name | Notes |
|---|---|---|
| Namn * | name | Required. Full name. |
| Typ * | kind | Required. freelancer = Frilansare, employee = Anställd, both = Båda. |
| Plats | location | Autocomplete widget (Tom Select) over a hidden text input. Always "City, Country", e.g. "Stockholm, Sweden", never just "Stockholm". |
| LinkedIn | linkedin_url | Full profile URL. |
| E-post | email | | 
| Telefon | phone | | 
| Kompetenser | skills | Comma-separated. See conventions. | 
| Beskrivning | description | Short summary. See conventions. |

## Conventions

### Kompetenser

A comma-separated list, usually sourced from the resume or a similar document.
10–15 skills is enough. It does not need to be exhaustive.
Most significant first: the skills the candidate has the most experience with, or that matter most for a hiring decision. For a developer, languages and core frameworks (Python, TypeScript, React) come before peripheral things (Active Directory, Scrum, Jira).
No duplicates (watch for case variants such as "TypeScript" / "Typescript").

### Plats

Always "City, Country" in English country form, e.g. "Malmö, Sweden", "Berlin, Germany".
After setting it, read back the hidden location input to confirm the stored value is the full "City, Country" string, not just the city. The widget can display a shorter label than the stored value, so on edits also check that an untouched location was not shortened.

### Beskrivning

A short summary of the candidate: role/seniority, main areas of experience, and anything notable for placement (e.g. freelance vs employment, availability, location constraints if known). A few sentences, not a copy of the resume.

### Resume

If a resume is available, always upload it.
The candidate must exist before a resume can be uploaded, so create first, then upload on the profile.

## Workflows

### Find a candidate

Open /candidates/?q=<name> and read the results.
If there are several matches (duplicates exist, e.g. the same person as both Anställd and Frilansare), list them with type, location and id and ask which one is meant.

### Create a candidate

Search first by name to avoid creating a duplicate. If a likely match exists, tell the user and ask whether to update it instead.

Extract the fields from the source (resume, LinkedIn text, user's message) following the conventions above. If Typ is unknown, ask.
Show the user the values to be saved and get a clear yes.
On /candidates/, click "Ny kandidat" (opens modal #candidate-create-modal), fill the fields, set Plats through the autocomplete, and click "Spara".
Confirm the new profile loaded and note its id (/candidates/<id>/).
If a resume is available, upload it (below).

### Edit a candidate

Open the profile and read the current values.
Show the user what will change (old → new) and get a clear yes.
Click "Redigera" (modal #candidate-edit-modal), change only the agreed fields, check the location value as described above, and click "Spara".
Re-read the profile to confirm the change.

### Upload a resume

Open the candidate's profile. The "CV" section has a file input (#resume-new-file, form posts to /candidates/<id>/resumes/new/) and a "Ladda upp" button.
The built-in browser has no file-picker tool. To attach a file from the conversation, put it into the input with javascript_tool: build a File from the file's bytes (base64), add it to a DataTransfer, and assign input.files = dt.files.
Confirm with the user, then click "Ladda upp".
Check that the file now appears in the CV table.
If attaching the file fails (for example the file is too large to pass in), ask the user to choose the file in the upload field in the browser pane and click "Ladda upp" themselves.

### Comment

On the profile, write in the "Kommentarer" field and click "Kommentera". Confirm the text with the user before posting.

### Flag or delete

Allowed only after explicit confirmation from the user for that specific action.

- Flagga: modal #candidate-flag-modal, with an optional reason (flag_reason).
- Ta bort (candidate): modal #candidate-delete-modal. Ta bort (resume): per-resume modal in the CV table.

Before asking, name exactly what will be flagged or deleted (candidate name, id, file name).

## Rules

- Confirm before every save, upload, comment, flag or delete. Reading, searching and filtering need no confirmation.
- Change only what the user asked for.
- Never sign out, change the account's settings or password, or act outside the candidate tasks the user asked for.
- After finishing, tell the user what was done, with the candidate's name and profile link.
