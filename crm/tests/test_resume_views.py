import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from crm.models import Resume

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def resume(candidate):
    return Resume.objects.create(
        candidate=candidate,
        file=ContentFile(b"%PDF-1.4 fake", name="cv.pdf"),
        filename="Sara Lind CV.pdf",
    )


def test_upload_resume_creates_resume(auth_client, candidate):
    upload = SimpleUploadedFile(
        "Sara Lind CV.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
    )
    response = auth_client.post(
        reverse("resume-create", args=[candidate.pk]), {"file": upload}
    )

    detail_url = reverse("candidate-detail", args=[candidate.pk])
    assert response.status_code == 302
    assert response.url == f"{detail_url}#resumes"

    resume = candidate.resumes.get()
    assert resume.filename == "Sara Lind CV.pdf"
    with resume.file.open("rb") as stored:
        assert stored.read() == b"%PDF-1.4 fake"


def test_upload_resume_without_file_flashes_error(auth_client, candidate):
    response = auth_client.post(
        reverse("resume-create", args=[candidate.pk]), {}, follow=True
    )
    assert candidate.resumes.count() == 0
    messages = [str(m) for m in response.context["messages"]]
    assert messages


def test_upload_resume_too_large_is_rejected(auth_client, candidate):
    upload = SimpleUploadedFile("huge.pdf", b"x" * (20 * 1024 * 1024 + 1))
    auth_client.post(reverse("resume-create", args=[candidate.pk]), {"file": upload})
    assert candidate.resumes.count() == 0


def test_upload_resume_requires_login(client, candidate):
    upload = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 fake")
    response = client.post(
        reverse("resume-create", args=[candidate.pk]), {"file": upload}
    )
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    assert candidate.resumes.count() == 0


def test_download_resume_serves_file_as_attachment(auth_client, resume):
    response = auth_client.get(reverse("resume-download", args=[resume.pk]))
    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"%PDF-1.4 fake"
    disposition = response.headers["Content-Disposition"]
    assert disposition.startswith("attachment")
    assert "Sara Lind CV.pdf" in disposition


def test_download_resume_requires_login(client, resume):
    response = client.get(reverse("resume-download", args=[resume.pk]))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


def test_download_missing_resume_404s(auth_client):
    response = auth_client.get(reverse("resume-download", args=[999]))
    assert response.status_code == 404


def test_delete_resume_removes_row_and_file(auth_client, resume):
    storage, name = resume.file.storage, resume.file.name
    assert storage.exists(name)

    response = auth_client.post(reverse("resume-delete", args=[resume.pk]))

    detail_url = reverse("candidate-detail", args=[resume.candidate_id])
    assert response.status_code == 302
    assert response.url == f"{detail_url}#resumes"
    assert not Resume.objects.filter(pk=resume.pk).exists()
    assert not storage.exists(name)


def test_deleting_candidate_deletes_resume_files(resume, candidate):
    storage, name = resume.file.storage, resume.file.name
    candidate.delete()
    assert not Resume.objects.exists()
    assert not storage.exists(name)


def test_candidate_detail_lists_resumes(auth_client, resume, candidate):
    response = auth_client.get(reverse("candidate-detail", args=[candidate.pk]))
    content = response.content.decode()
    assert "Sara Lind CV.pdf" in content
    assert reverse("resume-download", args=[resume.pk]) in content
