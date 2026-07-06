import pytest
from django.urls import reverse

from crm.models import Company, Contact, Lead, LeadComment


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
