import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Company, CompanyComment, Contact, Tag


@pytest.mark.django_db
def test_company_list_shows_companies_in_table(auth_client):
    Company.objects.create(name="Itancan Consulting", location="Stockholm")
    response = auth_client.get(reverse("company-list"))
    content = response.content.decode()
    assert "Itancan Consulting" in content
    assert "<table" in content


@pytest.mark.django_db
def test_company_list_shows_total_company_count(auth_client):
    Company.objects.create(name="Itancan Consulting", location="Stockholm")
    Company.objects.create(name="Datakraft", location="Göteborg")

    content = auth_client.get(
        reverse("company-list"), {"q": "Itancan"}
    ).content.decode()

    assert "2 företag" in content


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
def test_company_filter_by_multiple_tags_uses_and_semantics(auth_client):
    python = Tag.objects.create(name="Python")
    aws = Tag.objects.create(name="AWS")
    both = Company.objects.create(name="Båda AB")
    both.tags.add(python, aws)
    python_only = Company.objects.create(name="Python AB")
    python_only.tags.add(python)
    aws_only = Company.objects.create(name="AWS AB")
    aws_only.tags.add(aws)

    response = auth_client.get(
        reverse("company-list"), {"tags": [python.pk, aws.pk]}
    )

    assert [company.name for company in response.context["companies"]] == [
        "Båda AB"
    ]


@pytest.mark.django_db
def test_tag_filter_combines_with_search_and_assignee(auth_client, user):
    python = Tag.objects.create(name="Python")
    matching = Company.objects.create(
        name="Matchande konsultbolag", location="Stockholm", assignee=user
    )
    matching.tags.add(python)
    wrong_search = Company.objects.create(name="Annan verksamhet", assignee=user)
    wrong_search.tags.add(python)
    wrong_assignee = Company.objects.create(name="Konsultbolag utan ansvarig")
    wrong_assignee.tags.add(python)
    Company.objects.create(name="Konsultbolag utan Python", assignee=user)

    response = auth_client.get(
        reverse("company-list"),
        {"q": "konsultbolag", "assignee": user.pk, "tags": [python.pk]},
    )

    assert list(response.context["companies"]) == [matching]


@pytest.mark.django_db
def test_invalid_tag_filter_ids_are_ignored(auth_client):
    python = Tag.objects.create(name="Python")
    tagged = Company.objects.create(name="Taggat AB")
    tagged.tags.add(python)
    Company.objects.create(name="Utan tagg AB")

    response = auth_client.get(
        reverse("company-list"),
        {"tags": [str(python.pk), "not-an-id", "999999"]},
    )

    assert list(response.context["companies"]) == [tagged]
    assert response.context["current_tags"] == [str(python.pk)]


@pytest.mark.django_db
def test_company_free_text_search_does_not_search_tag_names(auth_client):
    python = Tag.objects.create(name="Python")
    company = Company.objects.create(name="Kodbolaget")
    company.tags.add(python)

    response = auth_client.get(reverse("company-list"), {"q": "Python"})

    assert list(response.context["companies"]) == []


@pytest.mark.django_db
def test_tag_parameters_survive_sort_and_pagination_links(auth_client):
    python = Tag.objects.create(name="Python")
    hot = Tag.objects.create(name="Hot")

    response = auth_client.get(
        reverse("company-list"),
        {"tags": [python.pk, hot.pk], "sort": "-name", "page": 1},
    )

    assert f"tags={python.pk}" in response.context["querystring"]
    assert f"tags={hot.pk}" in response.context["querystring"]
    assert "sort=-name" in response.context["querystring"]
    assert "page=" not in response.context["querystring"]
    assert f"tags={python.pk}" in response.context["sort_querystring"]
    assert f"tags={hot.pk}" in response.context["sort_querystring"]
    assert "sort=" not in response.context["sort_querystring"]


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
def test_company_list_sort_by_name_descending(auth_client):
    Company.objects.create(name="Öbergs Bygg")
    Company.objects.create(name="Zeta")
    Company.objects.create(name="Alfa")
    response = auth_client.get(reverse("company-list"), {"sort": "-name"})
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Öbergs Bygg", "Zeta", "Alfa"]


@pytest.mark.django_db
def test_company_list_sort_by_last_contacted_descending_puts_never_contacted_last(
    auth_client,
):
    now = timezone.now()
    Company.objects.create(name="Nyligen", last_contacted=now)
    Company.objects.create(name="Aldrig")
    Company.objects.create(
        name="Längesen", last_contacted=now - datetime.timedelta(days=30)
    )
    response = auth_client.get(
        reverse("company-list"), {"sort": "-last_contacted"}
    )
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Nyligen", "Längesen", "Aldrig"]


@pytest.mark.django_db
def test_company_list_unknown_sort_falls_back_to_name(auth_client):
    Company.objects.create(name="Zeta")
    Company.objects.create(name="Alfa")
    response = auth_client.get(reverse("company-list"), {"sort": "bogus"})
    companies = list(response.context["companies"])
    assert [c.name for c in companies] == ["Alfa", "Zeta"]


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
def test_create_company_with_existing_and_new_tags(auth_client):
    existing = Tag.objects.create(name="Python")

    response = auth_client.post(
        reverse("company-create"),
        {
            "name": "Taggat AB",
            "tag_names": [existing.name, " Hot ", "python"],
        },
    )

    assert response.status_code == 302
    company = Company.objects.get(name="Taggat AB")
    assert list(company.tags.values_list("name", flat=True)) == ["Hot", "Python"]
    assert Tag.objects.count() == 2


@pytest.mark.django_db
def test_invalid_company_does_not_create_tags(auth_client):
    auth_client.post(
        reverse("company-create"), {"name": "", "tag_names": ["Orphan"]}
    )

    assert not Tag.objects.filter(name="Orphan").exists()


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
def test_company_forms_render_tag_editor(auth_client, company):
    tag = Tag.objects.create(name="React")
    company.tags.add(tag)

    list_content = auth_client.get(reverse("company-list")).content.decode()
    detail_content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()

    assert "data-tag-input" in list_content
    assert "js/company_tags.js" in list_content
    assert "data-tag-input" in detail_content
    assert f'<option value="{tag.name}" selected>' in detail_content


@pytest.mark.django_db
def test_company_list_and_detail_render_tag_pills(auth_client, company):
    python = Tag.objects.create(name="Python")
    hot = Tag.objects.create(name="Hot")
    company.tags.add(python, hot)

    for url in [
        reverse("company-list"),
        reverse("company-detail", args=[company.pk]),
    ]:
        content = auth_client.get(url).content.decode()
        assert 'class="badge rounded-pill tag-pill"' in content
        hot_pill = '<span class="badge rounded-pill tag-pill">Hot</span>'
        python_pill = '<span class="badge rounded-pill tag-pill">Python</span>'
        assert content.index(hot_pill) < content.index(python_pill)


@pytest.mark.django_db
def test_company_list_renders_tag_filter(auth_client):
    python = Tag.objects.create(name="Python")

    content = auth_client.get(
        reverse("company-list"), {"tags": [python.pk]}
    ).content.decode()

    assert 'name="tags"' in content
    assert "data-tag-filter" in content
    assert re.search(rf'<option value="{python.pk}"\s+selected>', content)
    assert 'data-placeholder="Taggar"' in content


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
def test_edit_company_replaces_tags(auth_client):
    old = Tag.objects.create(name="Gammal")
    retained = Tag.objects.create(name="React")
    company = Company.objects.create(name="Taggat AB")
    company.tags.add(old, retained)

    response = auth_client.post(
        reverse("company-edit", args=[company.pk]),
        {"name": company.name, "tag_names": ["react", "Ny"]},
    )

    assert response.status_code == 302
    assert list(company.tags.values_list("name", flat=True)) == ["Ny", "React"]
    assert Tag.objects.filter(name="Gammal").exists()  # detached, not deleted


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
def test_log_contact_form_defaults_to_current_stockholm_datetime(
    auth_client, company, monkeypatch
):
    frozen_utc = datetime.datetime(
        2026, 8, 7, 7, 24, 37, tzinfo=datetime.UTC
    )
    monkeypatch.setattr(timezone, "now", lambda: frozen_utc)

    content = auth_client.get(
        reverse("company-detail", args=[company.pk])
    ).content.decode()

    assert 'type="datetime-local"' in content
    assert 'value="2026-08-07T09:24"' in content
    assert 'max="2026-08-07T09:24"' in content


@pytest.mark.django_db
def test_log_contact_sets_last_contacted_to_selected_datetime(auth_client, company):
    contacted_at = timezone.localtime(timezone.now() - datetime.timedelta(days=1))
    contacted_at = contacted_at.replace(second=0, microsecond=0)

    response = auth_client.post(
        reverse("company-log-contact", args=[company.pk]),
        {
            "contacted_at": contacted_at.strftime("%Y-%m-%dT%H:%M"),
            "comment": "",
        },
    )

    assert response.status_code == 302
    company.refresh_from_db()
    assert company.last_contacted == contacted_at
    assert company.comments.count() == 0


@pytest.mark.django_db
def test_log_contact_rejects_future_datetime(auth_client, company):
    previous_contact = timezone.now() - datetime.timedelta(days=2)
    company.last_contacted = previous_contact
    company.save(update_fields=["last_contacted"])
    future_contact = timezone.localtime(
        timezone.now() + datetime.timedelta(days=1)
    ).replace(second=0, microsecond=0)

    response = auth_client.post(
        reverse("company-log-contact", args=[company.pk]),
        {
            "contacted_at": future_contact.strftime("%Y-%m-%dT%H:%M"),
            "comment": "",
        },
        follow=True,
    )

    assert "Datum och tid kan inte vara i framtiden." in response.content.decode()
    company.refresh_from_db()
    assert company.last_contacted == previous_contact
    assert company.comments.count() == 0


@pytest.mark.django_db
def test_log_contact_with_comment_adds_comment(auth_client, user, company):
    contacted_at = timezone.localtime(timezone.now() - datetime.timedelta(days=1))
    auth_client.post(
        reverse("company-log-contact", args=[company.pk]),
        {
            "contacted_at": contacted_at.strftime("%Y-%m-%dT%H:%M"),
            "comment": "Ringde och bokade möte.",
        },
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
