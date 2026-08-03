# 015 — Candidate migration from Candide

One-time migration of candidate data from the old system, **Candide** (also a
Django app, hosted on the same VPS), into Cream. Covers candidates, their CV
files, and their comments. See `TODO.md` → "Transfer data from Candide".

## Approach

A **dumpdata JSON fixture** exported from Candide, plus Candide's media
directory copied manually into Cream, loaded by a custom management command in
Cream. Chosen over a direct DB-to-DB connection so the export is a decoupled,
auditable artifact and Cream never needs live access to Candide's database.

This is a **one-time cutover**, not an idempotent sync: run once against a
fresh Cream candidate table. The command therefore **aborts if candidates
already exist** (override with `--allow-nonempty`) so an accidental re-run
can't silently duplicate everything.

### Export from Candide (Docker Compose)

Candide and Cream run as separate Compose projects in sibling directories on
the same VPS. Run the export from Candide's Compose directory:

```sh
# App label is whatever Candide uses; dumping the whole app is fine.
docker compose exec -T web \
    python manage.py dumpdata candidates --indent 2 > candide.json
```

`-T` disables the pseudo-TTY so its formatting cannot leak into the redirected
JSON. The shell redirection happens on the host, so this creates
`candide.json` in Candide's Compose directory, not inside the container.

Candide's media is bind-mounted from a host directory. Find the media path
inside the container and the corresponding host path with:

```sh
docker compose exec -T web python manage.py shell -c \
    'from django.conf import settings; print(settings.MEDIA_ROOT)'

docker inspect "$(docker compose ps -q web)" \
    --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
```

In the second command's output, use the source (left-hand) path whose
destination matches `MEDIA_ROOT`. That source is the Candide media directory
used below; it must be the directory that directly contains `resumes/…`.

Keep `candide.json` together with access to that media directory. They are the
auditable source artifacts for the migration.

### Import into Cream (Docker Compose)

Before running the command, manually copy the **contents** of Candide's media
directory into Cream's host-side `data/media/` directory. Preserve the paths
from the fixture: a Candide file stored as `resumes/foo.pdf` must end up at
`<Cream Compose directory>/data/media/resumes/foo.pdf`.

For example, from Cream's Compose directory (the trailing slashes matter):

```sh
rsync -a /absolute/path/to/candide/media/ ./data/media/
```

Then run the import from Cream's Compose directory while its database is
running. Replace `/absolute/path/to/candide/candide.json` with the fixture's
absolute **host** path. The temporary one-off container mounts only the JSON
fixture read-only; Cream's normal media bind mount exposes the manually copied
files at `/app/media`.

```sh
docker compose run --rm --no-deps \
    -v /absolute/path/to/candide/candide.json:/candide-import/candide.json:ro \
    web python manage.py import_candide /candide-import/candide.json \
    --user <username>
```

`--no-deps` relies on Cream's existing `db` service; omit it if the Cream
stack is not already running and Compose should start dependencies. `--rm`
removes only the temporary command container when it finishes. It does not
remove either application's persistent data.

## The two schemas

Candide's `Candidate`, `Resume`, and `Comment` models were provided in full;
the mapping below is exhaustive against them.

### Candidate field mapping (Candide → Cream)

| Candide                     | Cream            | Notes                                                    |
| --------------------------- | ---------------- | -------------------------------------------------------- |
| `name`                      | `name`           | Direct. Cream's field is longer + Swedish-collated.      |
| `email`                     | `email`          | Direct.                                                  |
| `phone`                     | `phone`          | Direct.                                                  |
| `linkedin_url`              | `linkedin_url`   | Direct.                                                  |
| `location`                  | `location`       | Direct.                                                  |
| `skills`                    | `skills`         | Copied verbatim (see caveat below).                      |
| `employment_type`           | `kind`           | Value rename: `full_time` → `employee`; `freelancer` and `both` unchanged. Any other value is an error (fail loud). |
| `is_flagged` + `flag_reason`| `flagged_by` + `flag_reason` | See "Flag handling".                          |
| `created_at`, `updated_at`  | —                | Dropped: Cream's `Candidate` has no timestamp fields. Accepted data loss. |
| —                           | `description`    | Cream-only; left blank (Candide has no equivalent).      |

**Skills caveat:** both sides store `skills` as free text, so it's copied
verbatim. Cream's UI renders skills as chips by splitting on commas
(`Candidate.skills_list`). If Candide's data is newline- or otherwise-separated,
it will still import correctly but render as a single chip. This spec does
**not** attempt to reformat skills; flag it for manual review after import if
the chip display looks wrong.

### Flag handling

Cream has no `is_flagged` boolean — `Candidate.is_flagged` is a property that's
true iff `flagged_by` is set **or** `flag_reason` is non-empty. Candide's flags
carry no user, and some flagged candidates have an empty reason, so to preserve
every flag we attribute it to the **import user**:

- Candide `is_flagged == True` → set `flagged_by = <import user>` and copy
  `flag_reason` verbatim (may be empty; the user attribution keeps the flag
  alive).
- Candide `is_flagged == False` → leave `flagged_by = None`, `flag_reason = ""`.

### Resume / CV files (Candide → Cream)

Candide `Resume`: `candidate` FK, `file` (`upload_to="resumes/"`),
`uploaded_at`. Cream `Resume` additionally has a `filename` field (the original
upload name, used for display and as the download filename).

- The fixture's `file` value is a stored relative path like `resumes/foo.pdf`.
  Both systems root resume storage at `resumes/…`, so the path is copied
  **unchanged** into Cream's `Resume.file`. The file's bytes must already have
  been copied manually to `<Cream MEDIA_ROOT>/<file>`. (`upload_to` only
  governs *new* uploads; setting `.file` to an existing path directly is
  fine.)
- `filename` ← `os.path.basename(file)`.
- `uploaded_at`: Candide's value is preserved. (`auto_now_add` ignores values
  on normal saves, so the command sets it explicitly / via an update after
  insert. If preserving it proves awkward, falling back to import time is
  acceptable and should be noted, not silently done.)
- **Missing file on disk:** warn (with the candidate + path) and skip that one
  resume row; do not abort the whole run. Report the skipped count in the
  summary.

### Comments (Candide → Cream)

Candide `Comment`: `content` (≤1200 chars), `user` FK, `candidate` FK,
`created_at`. Cream's `CandidateComment` (a `BaseComment` subclass): `content`,
`user`, `candidate`, `created_at`, plus `edited_at` / `last_edited_by`.

- `content` ← copied verbatim.
- `candidate` ← the migrated candidate (via the id remap below).
- `user` ← the **import user** (all authors collapse to one user, per the
  migration decision — Candide user identities are not mapped).
- `created_at` ← preserved from Candide where practical (same `auto_now_add`
  caveat as resumes).
- `edited_at` / `last_edited_by` ← left null.

## The import user

`--user <username>` is **required**. The command looks the user up (Cream's
`User` model) and errors out if it doesn't exist. This single user becomes:

- the `flagged_by` on every flagged candidate, and
- the `user` (author) on every migrated comment.

Collapsing all authorship to one user is **lossless**, not just a
simplification: Candide only ever had one active user (the admin), so every
comment and flag in the source already belongs to that same person. Point
`--user` at the corresponding Cream admin account.

## Command behaviour

`import_candide <fixture.json> --user <username> [--allow-nonempty]`

1. Resolve the import user; error if missing.
2. Unless `--allow-nonempty`, abort if `Candidate.objects.exists()`.
3. Parse the fixture. Dispatch each object by the **suffix** of its `model`
   key (`.candidate`, `.resume`, `.comment`) so the command is agnostic to
   Candide's actual app label. Unknown models are ignored with a notice.
4. In a single `transaction.atomic()` block:
   - Create candidates, building an `old_pk → new Candidate` map.
   - Create resumes and comments, resolving their `candidate` FK through the
     map. Create a resume row only when its file already exists in Cream's
     `MEDIA_ROOT` (see missing-file handling).
5. Print a summary: N candidates, N resumes (M skipped for missing files), N
   comments.

Notes:
- **The manual file transfer is not transactional.** DB rows roll back on
  error, but the pre-copied files remain on disk. This is harmless for a
  one-time cutover.
- Candidate PKs are **remapped**, not forced, so the command doesn't depend on
  Cream's candidate table being empty at the DB level (only the `--allow-
  nonempty` guard enforces the intended fresh-cutover workflow).

## Tests

A focused automated test verifies that the command creates a resume row for a
file already present in Cream's `MEDIA_ROOT` without modifying the file, and
that candidate, resume, and comment primary keys are remapped. Remaining
correctness is protected by the command's fail-loud behaviour — unknown
`employment_type`, missing `--user`, and the non-empty guard all abort — plus
the printed summary (candidate / resume / comment counts, and skipped-file
count) for a manual sanity check after the run. Do a trial run against a
scratch Cream database before the real cutover.

## Out of scope

- Leads and lead–candidate associations (Candide's model has no leads).
- Companies/contacts (separate system in Cream; not in Candide's candidate app).
- Idempotent re-sync — this is a one-time cutover.
- Reformatting `skills` text into Cream's comma-separated convention.
- Migrating Candide user accounts / per-author comment attribution.
