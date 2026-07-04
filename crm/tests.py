import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


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
def test_logout_via_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    response = client.get(reverse("company-list"))
    assert response.status_code == 302
