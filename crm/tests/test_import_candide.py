import json
from io import StringIO

import pytest
from django.core.management import call_command

from crm.models import Candidate, CandidateComment, Resume


pytestmark = pytest.mark.django_db


def test_import_uses_resume_already_present_in_media_root(settings, tmp_path, user):
    source_candidate_pk = 900_017
    source_resume_pk = 900_023
    source_comment_pk = 900_029
    settings.MEDIA_ROOT = tmp_path / "media"
    resume_path = settings.MEDIA_ROOT / "resumes" / "sara-lind.pdf"
    resume_path.parent.mkdir(parents=True)
    resume_path.write_bytes(b"already copied")

    fixture_path = tmp_path / "candide.json"
    fixture_path.write_text(
        json.dumps(
            [
                    {
                        "model": "candidates.candidate",
                        "pk": source_candidate_pk,
                    "fields": {
                        "name": "Sara Lind",
                        "employment_type": "full_time",
                    },
                },
                    {
                        "model": "candidates.resume",
                        "pk": source_resume_pk,
                        "fields": {
                            "candidate": source_candidate_pk,
                            "file": "resumes/sara-lind.pdf",
                        },
                    },
                    {
                        "model": "candidates.comment",
                        "pk": source_comment_pk,
                        "fields": {
                            "candidate": source_candidate_pk,
                            "content": "Strong profile.",
                        },
                    },
            ]
        ),
        encoding="utf-8",
    )

    call_command(
        "import_candide",
        fixture_path,
        user=user.username,
        stdout=StringIO(),
    )

    candidate = Candidate.objects.get()
    resume = Resume.objects.get()
    comment = CandidateComment.objects.get()
    assert candidate.pk != source_candidate_pk
    assert resume.pk != source_resume_pk
    assert comment.pk != source_comment_pk
    assert resume.candidate == candidate
    assert comment.candidate == candidate
    assert resume.file.name == "resumes/sara-lind.pdf"
    assert resume.filename == "sara-lind.pdf"
    assert resume_path.read_bytes() == b"already copied"
