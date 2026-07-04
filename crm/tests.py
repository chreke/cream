import datetime

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from crm.models import Company


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="anna", password="x")

@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


def test_custom_user_model_is_active():
    assert get_user_model()._meta.label == "crm.User"


@pytest.mark.django_db
def test_create_user_with_username_email_password():
    user = get_user_model().objects.create_user(
        username="anna", email="anna@example.com", password="hemligt123"
    )
    assert user.username == "anna"
    assert user.email == "anna@example.com"
    assert user.check_password("hemligt123")
    assert user.password != "hemligt123"


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["company-list", "candidate-list", "pipeline"])
def test_views_require_login(client, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_redirects_to_company_list(client, django_user_model):
    django_user_model.objects.create_user(username="anna", password="hemligt123")
    response = client.post(
        reverse("login"), {"username": "anna", "password": "hemligt123"}
    )
    assert response.status_code == 302
    assert response.url == reverse("company-list")


@pytest.mark.django_db
def test_logged_in_user_sees_pages_and_own_username(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.get(reverse("company-list"))
    assert response.status_code == 200
    assert "anna" in response.content.decode()


@pytest.mark.django_db
def test_company_requires_only_name():
    company = Company.objects.create(name="Itancan Consulting")
    assert company.assignee is None
    assert company.last_contacted is None
    assert str(company) == "Itancan Consulting"


@pytest.mark.django_db
def test_company_list_shows_companies_in_table(auth_client):
    Company.objects.create(name="Itancan Consulting", location="Stockholm")
    response = auth_client.get(reverse("company-list"))
    content = response.content.decode()
    assert "Itancan Consulting" in content
    assert "<table" in content


@pytest.mark.django_db
def test_company_search_matches_name_and_location(auth_client):
    Company.objects.create(name="Itancan Consulting", location="Stockholm")
    Company.objects.create(name="Datakraft", location="Göteborg")
    Company.objects.create(name="Nordkod", location="Malmö")

    response = auth_client.get(reverse("company-list"), {"q": "itancan"})
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Itancan Consulting"]

    response = auth_client.get(reverse("company-list"), {"q": "göteborg"})
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Datakraft"]


@pytest.mark.django_db
def test_company_filter_by_assignee(auth_client, user, django_user_model):
    other = django_user_model.objects.create_user(username="bertil", password="x")
    Company.objects.create(name="Annas bolag", assignee=user)
    Company.objects.create(name="Bertils bolag", assignee=other)
    Company.objects.create(name="Ingens bolag")

    response = auth_client.get(reverse("company-list"), {"assignee": user.pk})
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Annas bolag"]


@pytest.mark.django_db
def test_company_list_sorts_by_name_by_default(auth_client):
    Company.objects.create(name="Zeta")
    Company.objects.create(name="Alfa")
    response = auth_client.get(reverse("company-list"))
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Alfa", "Zeta"]


@pytest.mark.django_db
def test_company_list_sort_by_last_contacted_puts_never_contacted_first(auth_client):
    now = timezone.now()
    Company.objects.create(name="Nyligen", last_contacted=now)
    Company.objects.create(name="Aldrig")
    Company.objects.create(
        name="Längesen", last_contacted=now - datetime.timedelta(days=30)
    )
    response = auth_client.get(
        reverse("company-list"), {"sort": "last_contacted"}
    )
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Aldrig", "Längesen", "Nyligen"]


@pytest.mark.django_db
def test_company_list_paginates_at_50(auth_client):
    for i in range(51):
        Company.objects.create(name=f"Bolag {i:03d}")
    response = auth_client.get(reverse("company-list"))
    assert len(response.context["companies"]) == 50
    response = auth_client.get(reverse("company-list"), {"page": 2})
    assert len(response.context["companies"]) == 1


@pytest.mark.django_db
def test_create_company_via_form(auth_client, user):
    response = auth_client.post(
        reverse("company-create"),
        {
            "name": "Itancan Consulting",
            "location": "Stockholm",
            "industry": "Konsultbolag",
            "homepage": "https://itancan.com",
            "organization_number": "556677-8899",
            "description": "Ett **konsultbolag**.",
            "assignee": user.pk,
        },
    )
    assert response.status_code == 302
    company = Company.objects.get(name="Itancan Consulting")
    assert company.assignee == user


@pytest.mark.django_db
def test_create_company_requires_name(auth_client):
    response = auth_client.post(reverse("company-create"), {"name": ""})
    assert response.status_code == 200
    assert Company.objects.count() == 0


@pytest.mark.django_db
def test_create_modal_renders_over_company_list(auth_client):
    Company.objects.create(name="Bakgrundsbolaget")
    response = auth_client.get(reverse("company-create"))
    content = response.content.decode()
    assert response.status_code == 200
    assert 'class="modal' in content
    assert "Nytt företag" in content
    assert "Bakgrundsbolaget" in content


@pytest.mark.django_db
def test_edit_modal_has_delete_button(auth_client):
    company = Company.objects.create(name="Bolaget")
    response = auth_client.get(reverse("company-edit", args=[company.pk]))
    content = response.content.decode()
    assert "Redigera företag" in content
    assert reverse("company-delete", args=[company.pk]) in content
    assert "Ta bort" in content


@pytest.mark.django_db
def test_delete_shows_confirmation_and_deletes_on_post(auth_client):
    company = Company.objects.create(name="Bolaget")

    response = auth_client.get(reverse("company-delete", args=[company.pk]))
    assert response.status_code == 200
    assert Company.objects.filter(pk=company.pk).exists()

    response = auth_client.post(reverse("company-delete", args=[company.pk]))
    assert response.status_code == 302
    assert not Company.objects.filter(pk=company.pk).exists()


@pytest.mark.django_db
def test_edit_company_via_form(auth_client):
    company = Company.objects.create(name="Gammalt namn")
    response = auth_client.post(
        reverse("company-edit", args=[company.pk]), {"name": "Nytt namn"}
    )
    assert response.status_code == 302
    company.refresh_from_db()
    assert company.name == "Nytt namn"


@pytest.mark.django_db
def test_logout_via_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    response = client.get(reverse("company-list"))
    assert response.status_code == 302
