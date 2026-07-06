import pytest
from django.contrib.auth import get_user_model

from crm.models import Company


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
def test_company_requires_only_name():
    company = Company.objects.create(name="Itancan Consulting")
    assert company.assignee is None
    assert company.last_contacted is None
    assert str(company) == "Itancan Consulting"
