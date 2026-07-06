import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Candidate, Company, CompanyComment, Contact


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
    # Swedish collation: Ö sorts after Z, not together with O.
    Company.objects.create(name="Öbergs Bygg")
    Company.objects.create(name="Zeta")
    Company.objects.create(name="Alfa")
    response = auth_client.get(reverse("company-list"))
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Alfa", "Zeta", "Öbergs Bygg"]


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
def test_company_list_embeds_create_modal(auth_client):
    Company.objects.create(name="Bakgrundsbolaget")
    response = auth_client.get(reverse("company-list"))
    content = response.content.decode()
    assert 'id="company-create-modal"' in content
    assert reverse("company-create") in content
    assert 'data-bs-target="#company-create-modal"' in content


@pytest.mark.django_db
def test_company_detail_embeds_edit_and_delete_modals(auth_client, company):
    response = auth_client.get(reverse("company-detail", args=[company.pk]))
    content = response.content.decode()
    assert 'id="company-edit-modal"' in content
    assert 'id="company-delete-modal"' in content
    assert 'value="Itancan Consulting"' in content  # edit form is pre-filled
    assert reverse("company-edit", args=[company.pk]) in content
    assert reverse("company-delete", args=[company.pk]) in content


@pytest.mark.django_db
def test_modal_form_get_urls_redirect(auth_client, company):
    contact = Contact.objects.create(company=company, name="Karin Berg")
    comment = CompanyComment.objects.create(company=company, content="x")
    detail_url = reverse("company-detail", args=[company.pk])
    assert auth_client.get(reverse("company-create")).url == reverse("company-list")
    for url_name, args in [
        ("company-edit", [company.pk]),
        ("company-delete", [company.pk]),
        ("company-log-contact", [company.pk]),
        ("contact-create", [company.pk]),
        ("contact-edit", [contact.pk]),
        ("contact-delete", [contact.pk]),
        ("company-comment-edit", [comment.pk]),
        ("company-comment-delete", [comment.pk]),
    ]:
        response = auth_client.get(reverse(url_name, args=args))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    assert Company.objects.filter(pk=company.pk).exists()
    assert Contact.objects.filter(pk=contact.pk).exists()
    assert CompanyComment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_invalid_create_reopens_modal_with_errors(auth_client):
    response = auth_client.post(reverse("company-create"), {"name": ""})
    content = response.content.decode()
    assert response.status_code == 200
    assert Company.objects.count() == 0
    assert "company-create-modal" in content
    assert "getOrCreateInstance" in content  # auto-open script rendered


@pytest.mark.django_db
def test_delete_company_on_post(auth_client, company):
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
def test_company_name_links_to_detail(auth_client, company):
    response = auth_client.get(reverse("company-list"))
    assert reverse("company-detail", args=[company.pk]) in response.content.decode()


@pytest.mark.django_db
def test_detail_shows_fields_and_action_buttons(auth_client, company):
    response = auth_client.get(reverse("company-detail", args=[company.pk]))
    content = response.content.decode()
    assert "Itancan Consulting" in content
    assert "Stockholm" in content
    assert "Logga kontakt" in content
    assert reverse("company-edit", args=[company.pk]) in content
    assert reverse("company-delete", args=[company.pk]) in content


@pytest.mark.django_db
def test_detail_renders_markdown_description(auth_client, company):
    company.description = "Ett **viktigt** bolag."
    company.save()
    response = auth_client.get(reverse("company-detail", args=[company.pk]))
    assert "<strong>viktigt</strong>" in response.content.decode()


@pytest.mark.django_db
def test_contact_create_via_modal(auth_client, company):
    response = auth_client.post(
        reverse("contact-create", args=[company.pk]),
        {
            "name": "Karin Berg",
            "role": "CTO",
            "linkedin_url": "https://linkedin.com/in/karinberg",
            "email": "karin@itancan.com",
            "phone": "070-1234567",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("company-detail", args=[company.pk])
    contact = company.contacts.get()
    assert contact.name == "Karin Berg"


@pytest.mark.django_db
def test_contact_shows_on_detail_with_edit_modal(auth_client, company):
    contact = Contact.objects.create(company=company, name="Karin Berg")
    content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()
    assert "Karin Berg" in content
    assert f'id="contact-edit-modal-{contact.pk}"' in content
    assert reverse("contact-edit", args=[contact.pk]) in content


@pytest.mark.django_db
def test_contact_edit_and_delete_on_post(auth_client, company):
    contact = Contact.objects.create(company=company, name="Karin Berg")

    response = auth_client.post(
        reverse("contact-edit", args=[contact.pk]), {"name": "Karin Berg-Ek"}
    )
    assert response.status_code == 302
    contact.refresh_from_db()
    assert contact.name == "Karin Berg-Ek"

    response = auth_client.post(reverse("contact-delete", args=[contact.pk]))
    assert response.status_code == 302
    assert not Contact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
def test_log_contact_sets_last_contacted(auth_client, company):
    response = auth_client.post(
        reverse("company-log-contact", args=[company.pk]), {"comment": ""}
    )
    assert response.status_code == 302
    company.refresh_from_db()
    assert company.last_contacted is not None
    assert company.comments.count() == 0


@pytest.mark.django_db
def test_log_contact_with_comment_adds_comment(auth_client, user, company):
    auth_client.post(
        reverse("company-log-contact", args=[company.pk]),
        {"comment": "Ringde och bokade möte."},
    )
    comment = company.comments.get()
    assert comment.content == "Ringde och bokade möte."
    assert comment.user == user


@pytest.mark.django_db
def test_add_comment_inline(auth_client, user, company):
    response = auth_client.post(
        reverse("company-comment-create", args=[company.pk]),
        {"content": "Bra möte idag."},
    )
    assert response.status_code == 302
    comment = company.comments.get()
    assert comment.user == user
    assert comment.edited_at is None


@pytest.mark.django_db
def test_edit_comment_stamps_editor(auth_client, user, company, django_user_model):
    author = django_user_model.objects.create_user(username="bertil", password="x")
    comment = CompanyComment.objects.create(
        company=company, user=author, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("company-comment-edit", args=[comment.pk]),
        {"content": "Ändrad text"},
    )
    assert response.status_code == 302
    assert response.url == reverse("company-detail", args=[company.pk])
    comment.refresh_from_db()
    assert comment.content == "Ändrad text"
    assert comment.user == author
    assert comment.edited_at is not None
    assert comment.last_edited_by == user


@pytest.mark.django_db
def test_comment_feed_shows_author_and_editor(auth_client, user, company):
    comment = CompanyComment.objects.create(
        company=company,
        user=user,
        content="En **kommentar**.",
        edited_at=timezone.now(),
        last_edited_by=user,
    )
    content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()
    assert "<strong>kommentar</strong>" in content
    assert "anna" in content
    assert "redigerad" in content
    assert f'id="comment-{comment.pk}"' in content  # anchor for scroll-into-view
    assert reverse("company-comment-edit", args=[comment.pk]) in content
    assert reverse("company-comment-delete", args=[comment.pk]) in content


@pytest.mark.django_db
def test_comment_feed_embeds_edit_modal(auth_client, user, company):
    comment = CompanyComment.objects.create(
        company=company, user=user, content="Ursprunglig text"
    )
    content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()
    assert f'id="comment-edit-modal-{comment.pk}"' in content
    assert "Ursprunglig text" in content  # edit form is pre-filled


@pytest.mark.django_db
def test_invalid_comment_edit_reopens_modal_with_errors(auth_client, user, company):
    comment = CompanyComment.objects.create(
        company=company, user=user, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("company-comment-edit", args=[comment.pk]), {"content": ""}
    )
    content = response.content.decode()
    assert response.status_code == 200
    assert f'getElementById("comment-edit-modal-{comment.pk}")' in content
    comment.refresh_from_db()
    assert comment.content == "Ursprunglig text"


@pytest.mark.django_db
def test_comment_feed_embeds_delete_confirmation_modal(auth_client, user, company):
    comment = CompanyComment.objects.create(
        company=company, user=user, content="Ska bort"
    )
    content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()
    assert f'id="comment-delete-modal-{comment.pk}"' in content

    response = auth_client.post(
        reverse("company-comment-delete", args=[comment.pk])
    )
    assert response.status_code == 302
    assert not CompanyComment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_candidate_list_shows_candidates_in_table(auth_client):
    Candidate.objects.create(
        name="Sara Lind",
        kind=Candidate.Kind.FREELANCER,
        location="Stockholm",
        linkedin_url="https://linkedin.com/in/saralind",
        skills="Python, Django",
    )
    content = auth_client.get(reverse("candidate-list")).content.decode()
    assert "<table" in content
    assert "Sara Lind" in content
    assert "Stockholm" in content
    assert "Frilansare" in content  # kind rendered as label
    assert "Python, Django" in content
    assert 'href="https://linkedin.com/in/saralind"' in content
    assert "bi-linkedin" in content  # rendered as an icon, not text


@pytest.mark.django_db
def test_candidate_list_truncates_long_skills(auth_client):
    Candidate.objects.create(
        name="Sara Lind",
        kind=Candidate.Kind.BOTH,
        skills=", ".join(f"Kompetens {i}" for i in range(20)),
    )
    content = auth_client.get(reverse("candidate-list")).content.decode()
    assert "Kompetens 19" not in content
    assert "…" in content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind_filter,expected",
    [
        ("", ["Anna Anställd", "Bo Båda", "Frida Frilans"]),
        ("freelancer", ["Bo Båda", "Frida Frilans"]),
        ("employee", ["Anna Anställd", "Bo Båda"]),
        ("both", ["Anna Anställd", "Bo Båda", "Frida Frilans"]),  # not filterable
    ],
)
def test_candidate_list_kind_filter_always_includes_both(
    auth_client, kind_filter, expected
):
    Candidate.objects.create(name="Frida Frilans", kind=Candidate.Kind.FREELANCER)
    Candidate.objects.create(name="Anna Anställd", kind=Candidate.Kind.EMPLOYEE)
    Candidate.objects.create(name="Bo Båda", kind=Candidate.Kind.BOTH)
    response = auth_client.get(reverse("candidate-list"), {"kind": kind_filter})
    assert [c.name for c in response.context["candidates"]] == expected


@pytest.mark.django_db
def test_logout_via_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    response = client.get(reverse("company-list"))
    assert response.status_code == 302
