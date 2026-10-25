from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Lead


def row_names(response):
    return [lead.name for lead in response.context["leads"]]


@pytest.mark.django_db
def test_lead_list_shows_columns_and_links(auth_client, company):
    lead = Lead.objects.create(
        name="Java-utvecklare",
        company=company,
        stage=Lead.Stage.WON,
        closed_at=date(2026, 3, 31),
    )
    response = auth_client.get(reverse("lead-list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert reverse("lead-detail", args=[lead.pk]) in content
    assert reverse("company-detail", args=[company.pk]) in content
    assert "Itancan Consulting" in content
    assert "Vunnen" in content
    assert "2026-03-31" in content


@pytest.mark.django_db
def test_lead_list_is_in_sidebar(auth_client):
    content = auth_client.get(reverse("company-list")).content.decode()
    assert reverse("lead-list") in content
    assert "Affärer" in content


@pytest.mark.django_db
def test_lead_list_requires_login(client):
    response = client.get(reverse("lead-list"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_lead_list_hides_deleted_leads_by_default(auth_client, company):
    Lead.objects.create(name="Aktiv", company=company)
    Lead.objects.create(name="Borttagen", company=company, deleted_at=timezone.now())
    response = auth_client.get(reverse("lead-list"))
    assert row_names(response) == ["Aktiv"]
    assert response.context["paginator"].count == 1


@pytest.mark.django_db
def test_lead_list_can_show_deleted_leads(auth_client, company):
    Lead.objects.create(name="Aktiv", company=company)
    Lead.objects.create(name="Borttagen", company=company, deleted_at=timezone.now())
    response = auth_client.get(reverse("lead-list"), {"deleted": "1"})
    assert row_names(response) == ["Aktiv", "Borttagen"]
    # Deleted rows are greyed out rather than badged.
    assert response.content.decode().count('class="row-deleted"') == 1


@pytest.mark.django_db
def test_lead_list_filters_by_stage(auth_client, company):
    Lead.objects.create(name="Vunnen affär", company=company, stage=Lead.Stage.WON)
    Lead.objects.create(name="Offert", company=company, stage=Lead.Stage.QUOTE)
    response = auth_client.get(reverse("lead-list"), {"stage": "won"})
    assert row_names(response) == ["Vunnen affär"]


@pytest.mark.django_db
def test_lead_list_ignores_unknown_stage(auth_client, company):
    Lead.objects.create(name="Offert", company=company, stage=Lead.Stage.QUOTE)
    response = auth_client.get(reverse("lead-list"), {"stage": "bogus"})
    assert row_names(response) == ["Offert"]


@pytest.mark.django_db
def test_lead_list_sorts_by_name_by_default(auth_client, company):
    for name in ["Örebro", "Bravo", "Alfa"]:
        Lead.objects.create(name=name, company=company)
    response = auth_client.get(reverse("lead-list"))
    assert row_names(response) == ["Alfa", "Bravo", "Örebro"]

    response = auth_client.get(reverse("lead-list"), {"sort": "-name"})
    assert row_names(response) == ["Örebro", "Bravo", "Alfa"]


@pytest.mark.django_db
def test_lead_list_sorts_by_won_date(auth_client, company):
    Lead.objects.create(name="Pågående", company=company)
    Lead.objects.create(
        name="Q1", company=company, stage=Lead.Stage.WON, closed_at=date(2026, 3, 1)
    )
    Lead.objects.create(
        name="Q3", company=company, stage=Lead.Stage.WON, closed_at=date(2026, 9, 1)
    )
    # Most recently won first; deals without a won date last either way.
    response = auth_client.get(reverse("lead-list"), {"sort": "-closed_at"})
    assert row_names(response) == ["Q3", "Q1", "Pågående"]

    response = auth_client.get(reverse("lead-list"), {"sort": "closed_at"})
    assert row_names(response) == ["Q1", "Q3", "Pågående"]


@pytest.mark.django_db
def test_lead_list_sort_links_preserve_filters(auth_client):
    content = auth_client.get(
        reverse("lead-list"), {"stage": "won", "deleted": "1", "sort": "-closed_at"}
    ).content.decode()
    # Clicking the active column reverses it; filters are kept.
    assert "?stage=won&amp;deleted=1&amp;sort=closed_at" in content
    assert "?stage=won&amp;deleted=1&amp;sort=name" in content
