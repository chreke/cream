"""Lead–candidate connection (specs/013): candidate section on the lead
page, attach/detach endpoints, and the picker's autocomplete endpoint."""

import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Candidate


@pytest.fixture
def candidate(db):
    return Candidate.objects.create(
        name="Erik Ek",
        kind=Candidate.Kind.FREELANCER,
        location="Stockholm",
        skills="Python, Django",
    )


@pytest.mark.django_db
def test_lead_detail_lists_attached_candidates(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "Kandidater" in content
    assert reverse("candidate-detail", args=[candidate.pk]) in content
    assert "Erik Ek" in content
    assert "Stockholm" in content
    assert "Python, Django" in content
    assert reverse("lead-candidate-detach", args=[lead.pk]) in content


@pytest.mark.django_db
def test_lead_detail_candidate_empty_state(auth_client, lead):
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "Inga kandidater" in content


@pytest.mark.django_db
def test_lead_detail_embeds_picker(auth_client, lead):
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "vendor/tom-select.complete.min.js" in content
    assert "vendor/tom-select.bootstrap5.min.css" in content
    assert "js/lead_candidates.js" in content
    assert reverse("lead-candidate-attach", args=[lead.pk]) in content
    assert reverse("lead-candidate-search", args=[lead.pk]) in content


@pytest.mark.django_db
def test_attach_candidate(auth_client, lead, candidate):
    url = reverse("lead-candidate-attach", args=[lead.pk])
    response = auth_client.post(url, {"candidate": candidate.pk})
    assert response.status_code == 302
    assert response.url == reverse("lead-detail", args=[lead.pk])
    assert list(lead.candidates.all()) == [candidate]

    # Idempotent: attaching again neither errors nor duplicates.
    response = auth_client.post(url, {"candidate": candidate.pk})
    assert response.status_code == 302
    assert list(lead.candidates.all()) == [candidate]


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [{}, {"candidate": "999"}, {"candidate": "x"}])
def test_attach_rejects_bad_candidate(auth_client, lead, payload):
    response = auth_client.post(
        reverse("lead-candidate-attach", args=[lead.pk]), payload
    )
    assert response.status_code == 404
    assert lead.candidates.count() == 0


@pytest.mark.django_db
def test_detach_candidate(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    url = reverse("lead-candidate-detach", args=[lead.pk])
    response = auth_client.post(url, {"candidate": candidate.pk})
    assert response.status_code == 302
    assert response.url == reverse("lead-detail", args=[lead.pk])
    assert lead.candidates.count() == 0
    # Candidate itself is untouched.
    assert Candidate.objects.filter(pk=candidate.pk).exists()

    # Detaching a non-attached candidate is a harmless no-op.
    response = auth_client.post(url, {"candidate": candidate.pk})
    assert response.status_code == 302


@pytest.mark.django_db
def test_candidate_search_returns_ranked_matches(auth_client, lead):
    Candidate.objects.create(
        name="Anna Andersson",
        kind=Candidate.Kind.EMPLOYEE,
        location="Göteborg",
        skills="Python",
    )
    Candidate.objects.create(
        name="Python Persson", kind=Candidate.Kind.EMPLOYEE, location="Malmö"
    )
    Candidate.objects.create(name="Ove Oberoende", kind=Candidate.Kind.EMPLOYEE)

    response = auth_client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "python"}
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert {r["name"] for r in results} == {"Anna Andersson", "Python Persson"}
    anna = next(r for r in results if r["name"] == "Anna Andersson")
    assert anna["location"] == "Göteborg"
    assert anna["skills"] == "Python"
    assert "id" in anna


@pytest.mark.django_db
def test_lead_page_truncates_long_skills(auth_client, lead, candidate):
    candidate.skills = ", ".join(f"Kompetens {i:02d}" for i in range(20))
    candidate.save()
    lead.candidates.add(candidate)
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "Kompetens 00" in content
    assert "Kompetens 19" not in content
    assert "…" in content


@pytest.mark.django_db
def test_candidate_search_truncates_long_skills(auth_client, lead, candidate):
    candidate.skills = ", ".join(f"Kompetens {i:02d}" for i in range(20))
    candidate.save()
    response = auth_client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "erik"}
    )
    (result,) = response.json()["results"]
    # Truncated on whole words, like the skills columns (truncatewords:10).
    assert result["skills"].endswith("…")
    assert "Kompetens 04" in result["skills"]
    assert "Kompetens 19" not in result["skills"]


@pytest.mark.django_db
def test_candidate_search_excludes_attached(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    response = auth_client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "erik"}
    )
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_candidate_search_caps_results_at_ten(auth_client, lead):
    for i in range(12):
        Candidate.objects.create(
            name=f"Kandidat {i:02d}", kind=Candidate.Kind.EMPLOYEE, skills="Java"
        )
    response = auth_client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "java"}
    )
    assert len(response.json()["results"]) == 10


@pytest.mark.django_db
def test_candidate_search_empty_query(auth_client, lead):
    response = auth_client.get(reverse("lead-candidate-search", args=[lead.pk]))
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_candidate_page_lists_leads_with_company(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert "Affärer" in content
    assert "Itancan Consulting" in content  # company name, the key signal
    assert reverse("lead-detail", args=[lead.pk]) in content
    assert lead.get_stage_display() in content


@pytest.mark.django_db
def test_candidate_page_marks_deleted_leads(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    lead.deleted_at = timezone.now()
    lead.save()
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    # Still listed and linked, but visibly marked.
    assert reverse("lead-detail", args=[lead.pk]) in content
    assert "Borttagen" in content


@pytest.mark.django_db
def test_candidate_page_leads_empty_state(auth_client, candidate):
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert "Affärer" in content
    assert "inte kopplad till några affärer" in content


@pytest.mark.django_db
def test_pipeline_card_shows_candidate_count(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "1 kandidat" in content


@pytest.mark.django_db
def test_candidate_search_requires_login(client, lead):
    response = client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "x"}
    )
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
