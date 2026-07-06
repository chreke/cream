import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model

from crm.models import Candidate, Company


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


@pytest.mark.django_db
def test_candidate_requires_only_name_and_kind():
    candidate = Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.FREELANCER
    )
    assert candidate.location == ""
    assert candidate.skills == ""
    assert candidate.flagged_by is None
    assert candidate.flag_reason == ""
    assert str(candidate) == "Sara Lind"


@pytest.mark.django_db
def test_candidates_ordered_by_name():
    Candidate.objects.create(name="Sara", kind=Candidate.Kind.BOTH)
    Candidate.objects.create(name="Erik", kind=Candidate.Kind.EMPLOYEE)
    assert [c.name for c in Candidate.objects.all()] == ["Erik", "Sara"]


def test_candidate_kind_choices():
    assert set(Candidate.Kind.values) == {"freelancer", "employee", "both"}


def test_candidate_registered_in_admin():
    assert admin.site.is_registered(Candidate)
