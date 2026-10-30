import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Candidate, Company, Lead


@pytest.fixture
def deleted_company():
    return Company.objects.create(
        name="Borttaget bolag", location="Kiruna", deleted_at=timezone.now()
    )


@pytest.fixture
def deleted_candidate():
    return Candidate.objects.create(
        name="Borttagen Kandidat",
        kind=Candidate.Kind.EMPLOYEE,
        location="Kiruna",
        deleted_at=timezone.now(),
    )


@pytest.mark.django_db
def test_company_list_hides_deleted_by_default(auth_client, company, deleted_company):
    response = auth_client.get(reverse("company-list"))
    assert list(response.context["companies"]) == [company]


@pytest.mark.django_db
def test_company_list_can_show_deleted(auth_client, company, deleted_company):
    response = auth_client.get(reverse("company-list"), {"deleted": "1"})
    assert set(response.context["companies"]) == {company, deleted_company}
    assert response.content.decode().count('class="row-deleted"') == 1


@pytest.mark.django_db
def test_candidate_list_hides_deleted_by_default(
    auth_client, candidate, deleted_candidate
):
    response = auth_client.get(reverse("candidate-list"))
    assert list(response.context["candidates"]) == [candidate]


@pytest.mark.django_db
def test_candidate_list_can_show_deleted(auth_client, candidate, deleted_candidate):
    response = auth_client.get(reverse("candidate-list"), {"deleted": "1"})
    assert set(response.context["candidates"]) == {candidate, deleted_candidate}
    assert response.content.decode().count('class="row-deleted"') == 1


@pytest.mark.django_db
def test_candidate_search_hides_deleted(auth_client, deleted_candidate):
    response = auth_client.get(reverse("candidate-list"), {"q": "Borttagen"})
    assert list(response.context["candidates"]) == []

    response = auth_client.get(
        reverse("candidate-list"), {"q": "Borttagen", "deleted": "1"}
    )
    assert list(response.context["candidates"]) == [deleted_candidate]


@pytest.mark.django_db
def test_deleted_company_detail_shows_banner_and_restore(auth_client, deleted_company):
    url = reverse("company-detail", args=[deleted_company.pk])
    content = auth_client.get(url).content.decode()
    assert "är borttaget" in content
    assert reverse("company-restore", args=[deleted_company.pk]) in content


@pytest.mark.django_db
def test_active_company_detail_has_no_restore(auth_client, company):
    url = reverse("company-detail", args=[company.pk])
    content = auth_client.get(url).content.decode()
    assert reverse("company-restore", args=[company.pk]) not in content


@pytest.mark.django_db
def test_deleted_candidate_detail_shows_banner_and_restore(
    auth_client, deleted_candidate
):
    url = reverse("candidate-detail", args=[deleted_candidate.pk])
    content = auth_client.get(url).content.decode()
    assert "är borttagen" in content
    assert reverse("candidate-restore", args=[deleted_candidate.pk]) in content


@pytest.mark.django_db
def test_active_candidate_detail_has_no_restore(auth_client, candidate):
    url = reverse("candidate-detail", args=[candidate.pk])
    content = auth_client.get(url).content.decode()
    assert reverse("candidate-restore", args=[candidate.pk]) not in content


@pytest.mark.django_db
def test_restore_company(auth_client, deleted_company):
    response = auth_client.post(reverse("company-restore", args=[deleted_company.pk]))
    assert response.url == reverse("company-detail", args=[deleted_company.pk])
    deleted_company.refresh_from_db()
    assert deleted_company.deleted_at is None


@pytest.mark.django_db
def test_restore_candidate(auth_client, deleted_candidate):
    response = auth_client.post(
        reverse("candidate-restore", args=[deleted_candidate.pk])
    )
    assert response.url == reverse("candidate-detail", args=[deleted_candidate.pk])
    deleted_candidate.refresh_from_db()
    assert deleted_candidate.deleted_at is None


@pytest.mark.django_db
def test_restore_requires_login(client, deleted_company, deleted_candidate):
    for url in [
        reverse("company-restore", args=[deleted_company.pk]),
        reverse("candidate-restore", args=[deleted_candidate.pk]),
    ]:
        response = client.post(url)
        assert response.url.startswith(reverse("login"))
    deleted_company.refresh_from_db()
    deleted_candidate.refresh_from_db()
    assert deleted_company.is_deleted
    assert deleted_candidate.is_deleted


@pytest.mark.django_db
def test_delete_modals_say_soft_deleted_objects_can_be_restored(
    auth_client, company, candidate, lead
):
    for url in [
        reverse("company-detail", args=[company.pk]),
        reverse("candidate-detail", args=[candidate.pk]),
        reverse("lead-detail", args=[lead.pk]),
    ]:
        assert "Det går att återställa" in auth_client.get(url).content.decode()


@pytest.mark.django_db
def test_location_options_exclude_deleted(auth_client, deleted_company, deleted_candidate):
    context = auth_client.get(reverse("candidate-list")).context
    assert "Kiruna" not in context["location_options"]
    assert "Kiruna" not in context["candidate_location_options"]


@pytest.mark.django_db
def test_lead_create_form_excludes_deleted_companies(
    auth_client, company, deleted_company
):
    form = auth_client.get(reverse("pipeline")).context["lead_create_form"]
    assert list(form.fields["company"].queryset) == [company]

    auth_client.post(
        reverse("lead-create"), {"name": "Ny affär", "company": deleted_company.pk}
    )
    assert not Lead.objects.filter(name="Ny affär").exists()


@pytest.mark.django_db
def test_lead_of_deleted_company_stays_and_is_marked(auth_client, lead):
    lead.company.deleted_at = timezone.now()
    lead.company.save()

    pipeline = auth_client.get(reverse("pipeline")).content.decode()
    assert lead.name in pipeline
    assert "Borttaget" in pipeline
    assert "Borttaget" in auth_client.get(reverse("lead-list")).content.decode()
    detail = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "Borttaget" in detail


@pytest.mark.django_db
def test_candidate_page_marks_leads_of_deleted_company(auth_client, lead, candidate):
    lead.candidates.add(candidate)
    lead.company.deleted_at = timezone.now()
    lead.company.save()
    url = reverse("candidate-detail", args=[candidate.pk])
    assert "Borttaget" in auth_client.get(url).content.decode()


@pytest.mark.django_db
def test_lead_page_marks_deleted_candidate(auth_client, lead, deleted_candidate):
    lead.candidates.add(deleted_candidate)
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert deleted_candidate.name in content
    assert "Borttagen" in content


@pytest.mark.django_db
def test_lead_candidate_search_excludes_deleted(auth_client, lead, deleted_candidate):
    response = auth_client.get(
        reverse("lead-candidate-search", args=[lead.pk]), {"q": "Borttagen"}
    )
    assert response.json() == {"results": []}


@pytest.mark.django_db
def test_deleted_candidate_cannot_be_attached_but_can_be_detached(
    auth_client, lead, deleted_candidate
):
    response = auth_client.post(
        reverse("lead-candidate-attach", args=[lead.pk]),
        {"candidate": deleted_candidate.pk},
    )
    assert response.status_code == 404
    assert not lead.candidates.exists()

    lead.candidates.add(deleted_candidate)
    auth_client.post(
        reverse("lead-candidate-detach", args=[lead.pk]),
        {"candidate": deleted_candidate.pk},
    )
    assert not lead.candidates.exists()
