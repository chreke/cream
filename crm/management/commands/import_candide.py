"""One-time migration of candidate data from the old system, Candide.

See specs/015-candide-migration.md. Loads a dumpdata JSON fixture exported
from Candide plus a copy of Candide's media directory, and creates the
corresponding Candidate / Resume / CandidateComment rows in Cream.

This is throwaway, run-once code: no automated tests, fail loud on anything
unexpected, and print a summary for a manual sanity check.
"""

import json
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from crm.models import Candidate, CandidateComment, Resume

# Candide's employment_type -> Cream's Candidate.kind. Only "full_time"
# differs in spelling; the rest are identical.
KIND_MAP = {
    "freelancer": Candidate.Kind.FREELANCER,
    "full_time": Candidate.Kind.EMPLOYEE,
    "both": Candidate.Kind.BOTH,
}


class Command(BaseCommand):
    help = "One-time import of candidates, CVs, and comments from Candide."

    def add_arguments(self, parser):
        parser.add_argument(
            "fixture",
            help="Path to the dumpdata JSON exported from Candide.",
        )
        parser.add_argument(
            "--media",
            required=True,
            help="Path to Candide's media directory (the tree containing "
            "resumes/…). Used to copy CV files.",
        )
        parser.add_argument(
            "--user",
            required=True,
            help="Username of the Cream user to attribute all imported "
            "comments and flags to (typically the admin).",
        )
        parser.add_argument(
            "--allow-nonempty",
            action="store_true",
            help="Proceed even if candidates already exist (default: abort, "
            "since this is a one-time cutover).",
        )

    def handle(self, *args, **options):
        import_user = self._resolve_user(options["user"])

        if not options["allow_nonempty"] and Candidate.objects.exists():
            raise CommandError(
                "Cream already has candidates; refusing to run a one-time "
                "import. Pass --allow-nonempty to override."
            )

        media_root = Path(options["media"])
        if not media_root.is_dir():
            raise CommandError(f"--media path is not a directory: {media_root}")

        objects = self._load_fixture(options["fixture"])
        candidates, resumes, comments = self._group(objects)

        with transaction.atomic():
            id_map = self._import_candidates(candidates, import_user)
            resumes_created, resumes_skipped = self._import_resumes(
                resumes, id_map, media_root
            )
            comments_created = self._import_comments(comments, id_map, import_user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(id_map)} candidates, "
                f"{resumes_created} resumes "
                f"({resumes_skipped} skipped for missing files), "
                f"{comments_created} comments."
            )
        )

    # --- helpers ---------------------------------------------------------

    def _resolve_user(self, username):
        User = get_user_model()
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"No Cream user with username {username!r}.")

    def _load_fixture(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Fixture not found: {path}")
        except json.JSONDecodeError as exc:
            raise CommandError(f"Fixture is not valid JSON: {exc}")

    def _group(self, objects):
        """Bucket dumpdata objects by the suffix of their `model` key so the
        command doesn't depend on Candide's app label."""
        candidates, resumes, comments = [], [], []
        buckets = {
            "candidate": candidates,
            "resume": resumes,
            "comment": comments,
        }
        for obj in objects:
            model = obj.get("model", "")
            name = model.split(".")[-1]
            bucket = buckets.get(name)
            if bucket is None:
                self.stdout.write(f"Ignoring unrecognised model: {model}")
                continue
            bucket.append(obj)
        return candidates, resumes, comments

    def _import_candidates(self, candidates, import_user):
        id_map = {}
        for obj in candidates:
            fields = obj["fields"]

            employment_type = fields["employment_type"]
            if employment_type not in KIND_MAP:
                raise CommandError(
                    f"Candidate pk={obj['pk']} has unknown employment_type "
                    f"{employment_type!r}."
                )

            is_flagged = fields.get("is_flagged", False)
            flag_reason = fields.get("flag_reason", "") if is_flagged else ""

            candidate = Candidate.objects.create(
                name=fields["name"],
                kind=KIND_MAP[employment_type],
                location=fields.get("location", ""),
                email=fields.get("email", ""),
                phone=fields.get("phone", ""),
                linkedin_url=fields.get("linkedin_url", ""),
                skills=fields.get("skills", ""),
                # Cream has no `description` equivalent in Candide.
                description="",
                # Attribute flags to the import user so Cream's derived
                # `is_flagged` stays true even when the reason is empty.
                flagged_by=import_user if is_flagged else None,
                flag_reason=flag_reason,
            )
            id_map[obj["pk"]] = candidate
        return id_map

    def _import_resumes(self, resumes, id_map, media_root):
        created = skipped = 0
        for obj in resumes:
            fields = obj["fields"]
            candidate = id_map.get(fields["candidate"])
            if candidate is None:
                self.stdout.write(
                    f"Ignoring resume pk={obj['pk']}: no candidate "
                    f"pk={fields['candidate']} in the fixture."
                )
                continue

            rel_path = fields["file"]
            src = media_root / rel_path
            if not src.is_file():
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping resume for {candidate.name}: file not "
                        f"found: {src}"
                    )
                )
                skipped += 1
                continue

            dst = Path(settings.MEDIA_ROOT) / rel_path
            os.makedirs(dst.parent, exist_ok=True)
            shutil.copy2(src, dst)

            resume = Resume.objects.create(
                candidate=candidate,
                file=rel_path,
                filename=os.path.basename(rel_path),
            )
            self._preserve_timestamp(Resume, resume.pk, "uploaded_at", fields)
            created += 1
        return created, skipped

    def _import_comments(self, comments, id_map, import_user):
        created = 0
        for obj in comments:
            fields = obj["fields"]
            candidate = id_map.get(fields["candidate"])
            if candidate is None:
                self.stdout.write(
                    f"Ignoring comment pk={obj['pk']}: no candidate "
                    f"pk={fields['candidate']} in the fixture."
                )
                continue

            comment = CandidateComment.objects.create(
                candidate=candidate,
                content=fields["content"],
                user=import_user,
            )
            self._preserve_timestamp(
                CandidateComment, comment.pk, "created_at", fields
            )
            created += 1
        return created

    def _preserve_timestamp(self, model, pk, field, fields):
        """Force an `auto_now_add` field to the Candide value.

        `auto_now_add` overrides any value on insert, so the original row is
        created first (with a now() timestamp) and then updated in place.
        """
        raw = fields.get(field)
        if not raw:
            return
        value = parse_datetime(raw)
        if value is not None:
            model.objects.filter(pk=pk).update(**{field: value})
