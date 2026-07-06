import pytest

from crm.models import Candidate, Company


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


@pytest.fixture
def candidate():
    return Candidate.objects.create(
        name="Sara Lind",
        kind=Candidate.Kind.FREELANCER,
        location="Stockholm",
        email="sara@example.com",
        phone="070-1234567",
        linkedin_url="https://linkedin.com/in/saralind",
        skills="Python, Django",
        description="En **grym** utvecklare.",
    )
