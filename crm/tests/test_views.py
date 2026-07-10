import pytest
from django.urls import reverse

from crm.models import Candidate, Company


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
def test_location_inputs_autocomplete_from_existing_values(auth_client):
    company = Company.objects.create(name="Öbergs Bygg", location="Göteborg")
    candidate = Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.BOTH, location="Malmö"
    )
    Company.objects.create(name="Tomt AB")  # blank location is excluded

    for url in [
        reverse("company-list"),
        reverse("company-detail", args=[company.pk]),
        reverse("candidate-list"),
        reverse("candidate-detail", args=[candidate.pk]),
    ]:
        content = auth_client.get(url).content.decode()
        # Tom Select picks up inputs marked data-location-input and reads
        # the suggestions from the json_script blob.
        assert "data-location-input" in content, url
        assert 'id="location-options" type="application/json"' in content, url
        assert "js/location_inputs.js" in content, url
        assert "vendor/tom-select.complete.min.js" in content, url
        # Locations from both models are suggested everywhere. json_script
        # writes ASCII-escaped JSON, so non-ASCII letters appear as \uXXXX.
        assert "G\\u00f6teborg" in content, url
        assert "Malm\\u00f6" in content, url
        assert "<datalist" not in content, url


@pytest.mark.django_db
def test_no_template_comments_leak_into_rendered_pages(
    auth_client, company, candidate, lead
):
    # Multi-line {# ... #} is not valid Django syntax and renders literally;
    # multi-line notes must use {% comment %} blocks (see CLAUDE.md).
    for url in [
        reverse("company-list"),
        reverse("company-detail", args=[company.pk]),
        reverse("candidate-list"),
        reverse("candidate-detail", args=[candidate.pk]),
        reverse("lead-detail", args=[lead.pk]),
        reverse("pipeline"),
    ]:
        content = auth_client.get(url).content.decode()
        assert "{#" not in content, url
        assert "#}" not in content, url


@pytest.mark.django_db
def test_logout_via_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    response = client.get(reverse("company-list"))
    assert response.status_code == 302
