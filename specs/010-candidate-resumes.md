# 010 — Candidate resumes

Upload one or more resume files (PDF, Word, anything) to a candidate, list
them on the candidate detail page, download them, and delete them. See
REQUIREMENTS.md § Resumes.

## Model

`Resume`:

- `candidate` — FK to `Candidate`, `CASCADE`, related name `resumes`
- `file` — `FileField(upload_to="resumes/%Y/%m/", max_length=255)`
- `filename` — the original name of the uploaded file. Django mangles the
  stored name (sanitization, dedup suffixes), so the original is kept
  separately for display and for the download filename.
- `uploaded_at` — `auto_now_add`

Ordering: newest first (matches comments). Registered in the admin.

Any file type is accepted (the requirement says "an arbitrary document"),
but uploads are capped at 20 MB to keep mistakes out.

### File cleanup

Django never deletes files from storage on its own. A `post_delete` signal
on `Resume` deletes `file` from storage; the signal also fires for rows
cascade-deleted with their candidate, which a `Model.delete()` override
would miss.

## Storage & serving

- `MEDIA_ROOT = BASE_DIR / "media"` (gitignored). Local disk is fine until
  deployment work says otherwise.
- **No public media URL.** `MEDIA_URL` is never routed, in DEBUG or
  otherwise. The only way to fetch a resume is the download view below,
  which sits behind `LoginRequiredMiddleware` like every other view.
- Download view: `GET /resumes/<pk>/download/` returns a `FileResponse`
  with `as_attachment=True` and the original `filename`. Attachment rather
  than inline: the files are untrusted arbitrary uploads, so don't let the
  browser render them in the app's origin.

## UI (candidate detail page)

A "CV:n" section between the description and the comments:

- Table of resumes: original filename (links to the download URL), upload
  date, and a delete button per row.
- Inline upload form (like the comment form — no modal for a single file
  input): `<input type="file" required>` + "Ladda upp" button. One file per
  submit; upload again for more.
- Delete goes through the shared `_confirm_delete_modal.html`.
- After upload/delete, redirect back to the detail page's `#resumes`
  anchor.

## URLs

- `candidates/<candidate_pk>/resumes/new/` → `resume-create` (POST)
- `resumes/<pk>/download/` → `resume-download` (GET)
- `resumes/<pk>/delete/` → `resume-delete` (POST)

## Tests

- Upload: creates the row, stores the file, records the original filename,
  redirects to `#resumes`; rejected when > 20 MB; anonymous users are
  redirected to login.
- Download: correct bytes, `Content-Disposition: attachment` with the
  original filename; anonymous users are redirected to login.
- Delete: removes the row and the file from storage.
- Deleting a candidate deletes its resume files from storage (cascade +
  signal).
- Detail page lists uploaded resumes.

Tests override `MEDIA_ROOT` to a tmp dir so they never touch `media/`.
