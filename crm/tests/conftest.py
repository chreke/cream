import pytest

from crm.models import Company


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="anna", password="x")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def company():
    return Company.objects.create(name="Itancan Consulting", location="Stockholm")
