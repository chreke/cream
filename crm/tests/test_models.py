import pytest
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
def test_candidates_ordered_by_name_with_swedish_collation():
    # Ö sorts after Z in Swedish; English-style collation would put it with O.
    Candidate.objects.create(name="Örjan", kind=Candidate.Kind.BOTH)
    Candidate.objects.create(name="Sara", kind=Candidate.Kind.EMPLOYEE)
    assert [c.name for c in Candidate.objects.all()] == ["Sara", "Örjan"]


def test_candidate_kind_choices():
    assert set(Candidate.Kind.values) == {"freelancer", "employee", "both"}


def test_candidate_skills_list_splits_and_strips():
    candidate = Candidate(skills=" Python,Django , ,SQL")
    assert candidate.skills_list == ["Python", "Django", "SQL"]
    assert Candidate(skills="").skills_list == []


@pytest.mark.django_db
def test_search_matches_whole_words_case_insensitively():
    Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.BOTH, skills="Java, Spring"
    )
    Candidate.objects.create(
        name="Erik Ek", kind=Candidate.Kind.BOTH, skills="JavaScript, React"
    )
    results = Candidate.objects.search("JAVA")
    assert [c.name for c in results] == ["Sara Lind"]  # no JavaScript near-miss


@pytest.mark.django_db
def test_search_targets_name_location_and_skills():
    Candidate.objects.create(name="Maria Malm", kind=Candidate.Kind.BOTH)
    Candidate.objects.create(
        name="Erik Ek", kind=Candidate.Kind.BOTH, location="Malmö"
    )
    Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.BOTH, skills="Python"
    )
    Candidate.objects.create(
        name="Ali Amir", kind=Candidate.Kind.BOTH, description="Kan Python."
    )
    assert [c.name for c in Candidate.objects.search("malm")] == ["Maria Malm"]
    assert [c.name for c in Candidate.objects.search("malmö")] == ["Erik Ek"]
    # Description is not searched.
    assert [c.name for c in Candidate.objects.search("python")] == ["Sara Lind"]


@pytest.mark.django_db
def test_search_requires_all_words_to_match():
    Candidate.objects.create(
        name="Sara Lind",
        kind=Candidate.Kind.BOTH,
        location="Stockholm",
        skills="Python",
    )
    Candidate.objects.create(
        name="Erik Ek", kind=Candidate.Kind.BOTH, location="Göteborg", skills="Python"
    )
    results = Candidate.objects.search("python stockholm")
    assert [c.name for c in results] == ["Sara Lind"]


@pytest.mark.django_db
def test_search_ranks_by_relevance_then_name():
    # "Örjan" mentions Java twice and outranks "Adam" despite name order.
    Candidate.objects.create(
        name="Örjan Öberg", kind=Candidate.Kind.BOTH, skills="Java, Java EE"
    )
    Candidate.objects.create(
        name="Adam Alm", kind=Candidate.Kind.BOTH, skills="Java"
    )
    assert [c.name for c in Candidate.objects.search("java")] == [
        "Örjan Öberg",
        "Adam Alm",
    ]

    # Equal relevance falls back to name order.
    Candidate.objects.all().delete()
    Candidate.objects.create(name="Bertil Berg", kind=Candidate.Kind.BOTH, skills="Go")
    Candidate.objects.create(name="Adam Alm", kind=Candidate.Kind.BOTH, skills="Go")
    assert [c.name for c in Candidate.objects.search("go")] == [
        "Adam Alm",
        "Bertil Berg",
    ]
