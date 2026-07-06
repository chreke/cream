import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import (
    Candidate,
    CandidateComment,
    Company,
    CompanyComment,
    Contact,
    Lead,
    LeadComment,
)


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
    assert response.status_code == 302
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
def test_invalid_create_flashes_errors_and_redirects(auth_client):
    response = auth_client.post(
        reverse("company-create"), {"name": ""}, follow=True
    )
    assert Company.objects.count() == 0
    assert response.redirect_chain == [(reverse("company-list"), 302)]
    assert "alert-danger" in response.content.decode()


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
    assert f'id="contact-{contact.pk}"' in content  # anchor for scroll-into-view
    assert f'id="contact-edit-modal-{contact.pk}"' in content
    assert reverse("contact-edit", args=[contact.pk]) in content


@pytest.mark.django_db
def test_contact_edit_and_delete_on_post(auth_client, company):
    contact = Contact.objects.create(company=company, name="Karin Berg")

    response = auth_client.post(
        reverse("contact-edit", args=[contact.pk]), {"name": "Karin Berg-Ek"}
    )
    assert response.status_code == 302
    detail_url = reverse("company-detail", args=[company.pk])
    assert response.url == f"{detail_url}#contact-{contact.pk}"
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
    detail_url = reverse("company-detail", args=[company.pk])
    assert response.url == f"{detail_url}#comment-{comment.pk}"
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
def test_invalid_comment_edit_flashes_errors_and_redirects(auth_client, user, company):
    comment = CompanyComment.objects.create(
        company=company, user=user, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("company-comment-edit", args=[comment.pk]), {"content": ""}, follow=True
    )
    detail_url = reverse("company-detail", args=[company.pk])
    assert response.redirect_chain == [(detail_url, 302)]
    assert "alert-danger" in response.content.decode()
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
def test_candidate_list_search_combines_with_kind_filter(auth_client):
    Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.FREELANCER, skills="Java"
    )
    Candidate.objects.create(name="Erik Ek", kind=Candidate.Kind.EMPLOYEE, skills="Java")
    Candidate.objects.create(
        name="Maria Malm", kind=Candidate.Kind.EMPLOYEE, skills="JavaScript"
    )
    response = auth_client.get(
        reverse("candidate-list"), {"q": "java", "kind": "employee"}
    )
    assert [c.name for c in response.context["candidates"]] == ["Erik Ek"]

    # Blank query is ignored.
    response = auth_client.get(reverse("candidate-list"), {"q": "   "})
    assert len(response.context["candidates"]) == 3


@pytest.mark.django_db
def test_candidate_list_links_to_detail(auth_client, candidate):
    content = auth_client.get(reverse("candidate-list")).content.decode()
    assert reverse("candidate-detail", args=[candidate.pk]) in content


@pytest.mark.django_db
def test_candidate_detail_shows_fields_with_links_and_badges(auth_client, candidate):
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert "Sara Lind" in content
    assert "Frilansare" in content
    assert "Stockholm" in content
    assert 'href="mailto:sara@example.com"' in content
    assert 'href="tel:070-1234567"' in content
    assert 'href="https://linkedin.com/in/saralind"' in content
    assert "bi-linkedin" in content
    assert '<span class="badge' in content  # skills as badges
    assert "<strong>grym</strong>" in content  # Markdown description


@pytest.mark.django_db
def test_candidate_detail_embeds_edit_and_delete_modals(auth_client, candidate):
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert 'id="candidate-edit-modal"' in content
    assert 'id="candidate-delete-modal"' in content
    assert 'value="Sara Lind"' in content  # edit form is pre-filled
    assert reverse("candidate-edit", args=[candidate.pk]) in content
    assert reverse("candidate-delete", args=[candidate.pk]) in content


@pytest.mark.django_db
def test_candidate_list_embeds_create_modal(auth_client):
    content = auth_client.get(reverse("candidate-list")).content.decode()
    assert 'id="candidate-create-modal"' in content
    assert reverse("candidate-create") in content


@pytest.mark.django_db
def test_create_candidate_redirects_to_new_detail_page(auth_client):
    response = auth_client.post(
        reverse("candidate-create"),
        {"name": "Erik Ek", "kind": "employee", "skills": "Java"},
    )
    assert response.status_code == 302
    candidate = Candidate.objects.get(name="Erik Ek")
    assert response.url == reverse("candidate-detail", args=[candidate.pk])


@pytest.mark.django_db
def test_invalid_candidate_create_flashes_errors_and_redirects(auth_client):
    response = auth_client.post(
        reverse("candidate-create"), {"name": "Erik Ek"}, follow=True
    )
    assert Candidate.objects.count() == 0
    assert response.redirect_chain == [(reverse("candidate-list"), 302)]
    assert "alert-danger" in response.content.decode()


@pytest.mark.django_db
def test_edit_candidate_via_form(auth_client, candidate):
    response = auth_client.post(
        reverse("candidate-edit", args=[candidate.pk]),
        {"name": "Sara Lind-Ek", "kind": "both"},
    )
    assert response.status_code == 302
    assert response.url == reverse("candidate-detail", args=[candidate.pk])
    candidate.refresh_from_db()
    assert candidate.name == "Sara Lind-Ek"
    assert candidate.kind == Candidate.Kind.BOTH


@pytest.mark.django_db
def test_delete_candidate_on_post(auth_client, candidate):
    response = auth_client.post(reverse("candidate-delete", args=[candidate.pk]))
    assert response.status_code == 302
    assert response.url == reverse("candidate-list")
    assert not Candidate.objects.filter(pk=candidate.pk).exists()


@pytest.mark.django_db
def test_candidate_modal_form_get_urls_redirect(auth_client, candidate):
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    assert auth_client.get(reverse("candidate-create")).url == reverse(
        "candidate-list"
    )
    for url_name in ["candidate-edit", "candidate-delete"]:
        response = auth_client.get(reverse(url_name, args=[candidate.pk]))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    assert Candidate.objects.filter(pk=candidate.pk).exists()


@pytest.mark.django_db
def test_flag_candidate_sets_flagger_and_reason(auth_client, user, candidate):
    response = auth_client.post(
        reverse("candidate-flag", args=[candidate.pk]),
        {"flag_reason": "Svarar inte på mejl."},
    )
    assert response.status_code == 302
    assert response.url == reverse("candidate-detail", args=[candidate.pk])
    candidate.refresh_from_db()
    assert candidate.flagged_by == user
    assert candidate.flag_reason == "Svarar inte på mejl."
    assert candidate.is_flagged


@pytest.mark.django_db
def test_flag_candidate_reason_is_optional(auth_client, user, candidate):
    auth_client.post(reverse("candidate-flag", args=[candidate.pk]), {})
    candidate.refresh_from_db()
    assert candidate.flagged_by == user
    assert candidate.flag_reason == ""
    assert candidate.is_flagged


@pytest.mark.django_db
def test_edit_flag_reason_keeps_original_flagger(
    auth_client, candidate, django_user_model
):
    flagger = django_user_model.objects.create_user(username="bertil", password="x")
    candidate.flagged_by = flagger
    candidate.flag_reason = "Gammal anledning"
    candidate.save()
    auth_client.post(
        reverse("candidate-flag", args=[candidate.pk]),
        {"flag_reason": "Ny anledning"},
    )
    candidate.refresh_from_db()
    assert candidate.flagged_by == flagger
    assert candidate.flag_reason == "Ny anledning"


@pytest.mark.django_db
def test_unflag_clears_flagger_and_reason(auth_client, user, candidate):
    candidate.flagged_by = user
    candidate.flag_reason = "En anledning"
    candidate.save()
    response = auth_client.post(reverse("candidate-unflag", args=[candidate.pk]))
    assert response.status_code == 302
    assert response.url == reverse("candidate-detail", args=[candidate.pk])
    candidate.refresh_from_db()
    assert candidate.flagged_by is None
    assert candidate.flag_reason == ""
    assert not candidate.is_flagged


@pytest.mark.django_db
def test_flagged_candidate_detail_shows_banner_and_modals(
    auth_client, user, candidate
):
    candidate.flagged_by = user
    candidate.flag_reason = "Svarar inte på mejl."
    candidate.save()
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert "Flaggad" in content
    assert "anna" in content  # who flagged
    assert "Svarar inte på mejl." in content
    assert 'id="candidate-flag-modal"' in content  # edit-reason modal
    assert 'id="candidate-unflag-modal"' in content  # remove confirmation
    assert reverse("candidate-flag", args=[candidate.pk]) in content
    assert reverse("candidate-unflag", args=[candidate.pk]) in content


@pytest.mark.django_db
def test_unflagged_candidate_detail_offers_flag_button(auth_client, candidate):
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert 'data-bs-target="#candidate-flag-modal"' in content
    assert reverse("candidate-flag", args=[candidate.pk]) in content
    assert "Flaggad" not in content
    assert reverse("candidate-unflag", args=[candidate.pk]) not in content


@pytest.mark.django_db
def test_candidate_list_marks_flagged_candidates(auth_client, user, candidate):
    Candidate.objects.create(name="Erik Ek", kind=Candidate.Kind.EMPLOYEE)
    candidate.flagged_by = user
    candidate.save()
    content = auth_client.get(reverse("candidate-list")).content.decode()
    # Only the flagged candidate's row gets the flag icon.
    assert content.count("bi-flag-fill") == 1


@pytest.mark.django_db
def test_flag_modal_get_urls_redirect(auth_client, user, candidate):
    candidate.flagged_by = user
    candidate.save()
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    for url_name in ["candidate-flag", "candidate-unflag"]:
        response = auth_client.get(reverse(url_name, args=[candidate.pk]))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    candidate.refresh_from_db()
    assert candidate.is_flagged  # GET must not unflag


@pytest.mark.django_db
def test_add_candidate_comment_redirects_to_anchor(auth_client, user, candidate):
    response = auth_client.post(
        reverse("candidate-comment-create", args=[candidate.pk]),
        {"content": "Bra intervju."},
    )
    assert response.status_code == 302
    comment = candidate.comments.get()
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    assert response.url == f"{detail_url}#comment-{comment.pk}"
    assert comment.user == user
    assert comment.edited_at is None


@pytest.mark.django_db
def test_edit_candidate_comment_stamps_editor(
    auth_client, user, candidate, django_user_model
):
    author = django_user_model.objects.create_user(username="bertil", password="x")
    comment = CandidateComment.objects.create(
        candidate=candidate, user=author, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("candidate-comment-edit", args=[comment.pk]),
        {"content": "Ändrad text"},
    )
    assert response.status_code == 302
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    assert response.url == f"{detail_url}#comment-{comment.pk}"
    comment.refresh_from_db()
    assert comment.content == "Ändrad text"
    assert comment.user == author
    assert comment.edited_at is not None
    assert comment.last_edited_by == user


@pytest.mark.django_db
def test_candidate_comment_feed_embeds_modals(auth_client, user, candidate):
    comment = CandidateComment.objects.create(
        candidate=candidate, user=user, content="En **kommentar**."
    )
    content = auth_client.get(
        reverse("candidate-detail", args=[candidate.pk])
    ).content.decode()
    assert "<strong>kommentar</strong>" in content
    assert "anna" in content
    assert f'id="comment-{comment.pk}"' in content
    assert f'id="comment-edit-modal-{comment.pk}"' in content
    assert f'id="comment-delete-modal-{comment.pk}"' in content
    assert "En **kommentar**." in content  # edit form is pre-filled
    assert reverse("candidate-comment-edit", args=[comment.pk]) in content
    assert reverse("candidate-comment-delete", args=[comment.pk]) in content


@pytest.mark.django_db
def test_invalid_candidate_comment_edit_flashes_errors(auth_client, user, candidate):
    comment = CandidateComment.objects.create(
        candidate=candidate, user=user, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("candidate-comment-edit", args=[comment.pk]),
        {"content": ""},
        follow=True,
    )
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    assert response.redirect_chain == [(detail_url, 302)]
    assert "alert-danger" in response.content.decode()
    comment.refresh_from_db()
    assert comment.content == "Ursprunglig text"


@pytest.mark.django_db
def test_delete_candidate_comment_on_post(auth_client, user, candidate):
    comment = CandidateComment.objects.create(
        candidate=candidate, user=user, content="Ska bort"
    )
    response = auth_client.post(
        reverse("candidate-comment-delete", args=[comment.pk])
    )
    assert response.status_code == 302
    assert not CandidateComment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_candidate_comment_get_urls_redirect(auth_client, candidate):
    comment = CandidateComment.objects.create(candidate=candidate, content="x")
    detail_url = reverse("candidate-detail", args=[candidate.pk])
    for url_name, args in [
        ("candidate-comment-create", [candidate.pk]),
        ("candidate-comment-edit", [comment.pk]),
        ("candidate-comment-delete", [comment.pk]),
    ]:
        response = auth_client.get(reverse(url_name, args=args))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    assert CandidateComment.objects.filter(pk=comment.pk).exists()


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
        assert 'list="location-options"' in content, url
        assert '<datalist id="location-options">' in content, url
        # Locations from both models are suggested everywhere.
        assert '<option value="Göteborg">' in content, url
        assert '<option value="Malmö">' in content, url


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
def test_pipeline_page_embeds_lead_create_modal(auth_client):
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "Ny affär" in content
    assert 'id="lead-create-modal"' in content
    assert reverse("lead-create") in content


@pytest.mark.django_db
def test_create_lead_redirects_to_new_detail_page(auth_client, company):
    response = auth_client.post(
        reverse("lead-create"),
        {"name": "Java-utvecklare", "company": company.pk},
    )
    assert response.status_code == 302
    lead = Lead.objects.get(name="Java-utvecklare")
    assert response.url == reverse("lead-detail", args=[lead.pk])
    assert lead.stage == Lead.Stage.IN_PROGRESS


@pytest.mark.django_db
def test_invalid_lead_create_flashes_errors_and_redirects(auth_client):
    response = auth_client.post(
        reverse("lead-create"), {"name": "Namnlös affär"}, follow=True
    )
    assert Lead.objects.count() == 0
    assert response.redirect_chain == [(reverse("pipeline"), 302)]
    assert "alert-danger" in response.content.decode()


@pytest.mark.django_db
def test_lead_detail_shows_fields_and_modals(auth_client, company, user, lead):
    contact = Contact.objects.create(company=company, name="Karin Berg")
    lead.contact = contact
    lead.save()
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "Java-utvecklare" in content
    assert "Pågående" in content  # stage badge
    assert "100\xa0000 kr" in content  # formatted expected value
    assert "Karin Berg" in content
    assert "anna" in content  # assignee
    # Company is linked.
    assert reverse("company-detail", args=[company.pk]) in content
    assert "Itancan Consulting" in content
    # Edit and delete modals are embedded.
    assert 'id="lead-edit-modal"' in content
    assert 'id="lead-delete-modal"' in content
    assert reverse("lead-edit", args=[lead.pk]) in content
    assert reverse("lead-delete", args=[lead.pk]) in content


@pytest.mark.django_db
def test_edit_lead_via_form(auth_client, company, lead):
    contact = Contact.objects.create(company=company, name="Karin Berg")
    response = auth_client.post(
        reverse("lead-edit", args=[lead.pk]),
        {
            "name": ".NET-utvecklare",
            "expected_value": "50000",
            "contact": contact.pk,
            "stage": "quote",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("lead-detail", args=[lead.pk])
    lead.refresh_from_db()
    assert lead.name == ".NET-utvecklare"
    assert lead.expected_value == 50000
    assert lead.contact == contact
    assert lead.stage == Lead.Stage.QUOTE


@pytest.mark.django_db
def test_lead_company_cannot_be_changed(auth_client, company, lead):
    other = Company.objects.create(name="Annat AB")
    auth_client.post(
        reverse("lead-edit", args=[lead.pk]),
        {"name": "Java-utvecklare", "stage": "in_progress", "company": other.pk},
    )
    lead.refresh_from_db()
    assert lead.company == company


@pytest.mark.django_db
def test_lead_contact_options_limited_to_own_company(auth_client, company, lead):
    own = Contact.objects.create(company=company, name="Karin Berg")
    other = Company.objects.create(name="Annat AB")
    foreign = Contact.objects.create(company=other, name="Bo Ek")

    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert f'value="{own.pk}"' in content
    assert "Karin Berg" in content
    assert "Bo Ek" not in content

    # A foreign contact is rejected server-side too.
    response = auth_client.post(
        reverse("lead-edit", args=[lead.pk]),
        {"name": "Java-utvecklare", "stage": "in_progress", "contact": foreign.pk},
        follow=True,
    )
    assert response.redirect_chain == [
        (reverse("lead-detail", args=[lead.pk]), 302)
    ]
    assert "alert-danger" in response.content.decode()
    lead.refresh_from_db()
    assert lead.contact is None


@pytest.mark.django_db
def test_delete_lead_on_post(auth_client, lead):
    response = auth_client.post(reverse("lead-delete", args=[lead.pk]))
    assert response.status_code == 302
    assert response.url == reverse("pipeline")
    assert not Lead.objects.filter(pk=lead.pk).exists()


@pytest.mark.django_db
def test_lead_modal_form_get_urls_redirect(auth_client, lead):
    assert auth_client.get(reverse("lead-create")).url == reverse("pipeline")
    detail_url = reverse("lead-detail", args=[lead.pk])
    for url_name in ["lead-edit", "lead-delete"]:
        response = auth_client.get(reverse(url_name, args=[lead.pk]))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    assert Lead.objects.filter(pk=lead.pk).exists()


@pytest.mark.django_db
def test_add_lead_comment_redirects_to_anchor(auth_client, user, lead):
    response = auth_client.post(
        reverse("lead-comment-create", args=[lead.pk]),
        {"content": "Kunden vill ha offert."},
    )
    assert response.status_code == 302
    comment = lead.comments.get()
    detail_url = reverse("lead-detail", args=[lead.pk])
    assert response.url == f"{detail_url}#comment-{comment.pk}"
    assert comment.user == user
    assert comment.edited_at is None


@pytest.mark.django_db
def test_edit_lead_comment_stamps_editor(auth_client, user, lead, django_user_model):
    author = django_user_model.objects.create_user(username="bertil", password="x")
    comment = LeadComment.objects.create(
        lead=lead, user=author, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("lead-comment-edit", args=[comment.pk]),
        {"content": "Ändrad text"},
    )
    assert response.status_code == 302
    detail_url = reverse("lead-detail", args=[lead.pk])
    assert response.url == f"{detail_url}#comment-{comment.pk}"
    comment.refresh_from_db()
    assert comment.content == "Ändrad text"
    assert comment.user == author
    assert comment.edited_at is not None
    assert comment.last_edited_by == user


@pytest.mark.django_db
def test_lead_comment_feed_embeds_modals(auth_client, user, lead):
    comment = LeadComment.objects.create(
        lead=lead, user=user, content="En **kommentar**."
    )
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert "<strong>kommentar</strong>" in content
    assert f'id="comment-{comment.pk}"' in content
    assert f'id="comment-edit-modal-{comment.pk}"' in content
    assert f'id="comment-delete-modal-{comment.pk}"' in content
    assert "En **kommentar**." in content  # edit form is pre-filled
    assert reverse("lead-comment-edit", args=[comment.pk]) in content
    assert reverse("lead-comment-delete", args=[comment.pk]) in content


@pytest.mark.django_db
def test_invalid_lead_comment_edit_flashes_errors(auth_client, user, lead):
    comment = LeadComment.objects.create(
        lead=lead, user=user, content="Ursprunglig text"
    )
    response = auth_client.post(
        reverse("lead-comment-edit", args=[comment.pk]),
        {"content": ""},
        follow=True,
    )
    detail_url = reverse("lead-detail", args=[lead.pk])
    assert response.redirect_chain == [(detail_url, 302)]
    assert "alert-danger" in response.content.decode()
    comment.refresh_from_db()
    assert comment.content == "Ursprunglig text"


@pytest.mark.django_db
def test_delete_lead_comment_on_post(auth_client, user, lead):
    comment = LeadComment.objects.create(lead=lead, user=user, content="Ska bort")
    response = auth_client.post(reverse("lead-comment-delete", args=[comment.pk]))
    assert response.status_code == 302
    assert not LeadComment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_lead_comment_get_urls_redirect(auth_client, lead):
    comment = LeadComment.objects.create(lead=lead, content="x")
    detail_url = reverse("lead-detail", args=[lead.pk])
    for url_name, args in [
        ("lead-comment-create", [lead.pk]),
        ("lead-comment-edit", [comment.pk]),
        ("lead-comment-delete", [comment.pk]),
    ]:
        response = auth_client.get(reverse(url_name, args=args))
        assert response.status_code == 302, url_name
        assert response.url == detail_url, url_name
    assert LeadComment.objects.filter(pk=comment.pk).exists()


@pytest.mark.django_db
def test_logout_via_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="anna", password="x")
    client.force_login(user)
    response = client.post(reverse("logout"))
    assert response.status_code == 302
    assert response.url == reverse("login")
    response = client.get(reverse("company-list"))
    assert response.status_code == 302
