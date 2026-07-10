import pytest
from django.urls import reverse
from django.utils import timezone

from crm.models import Company, Contact, Lead, LeadComment


@pytest.mark.django_db
def test_pipeline_page_embeds_lead_create_modal(auth_client):
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "Ny affär" in content
    assert 'id="lead-create-modal"' in content
    assert reverse("lead-create") in content


def column_segment(content, stage):
    """The chunk of pipeline-page HTML belonging to one stage's column."""
    after = content.split(f'id="stage-{stage}"', 1)[1]
    return after.split('id="stage-', 1)[0]


@pytest.mark.django_db
def test_pipeline_board_shows_all_stage_columns(auth_client):
    content = auth_client.get(reverse("pipeline")).content.decode()
    for stage, label in Lead.Stage.choices:
        assert f'id="stage-{stage}"' in content
        assert label in content


@pytest.mark.django_db
def test_pipeline_board_groups_leads_by_stage(auth_client, company):
    Lead.objects.create(
        name="Java-utvecklare", company=company, stage=Lead.Stage.QUOTE
    )
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "Java-utvecklare" in column_segment(content, "quote")
    assert "Java-utvecklare" not in column_segment(content, "in_progress")


@pytest.mark.django_db
def test_pipeline_board_card_shows_company_value_and_detail_link(
    auth_client, company, lead
):
    content = auth_client.get(reverse("pipeline")).content.decode()
    segment = column_segment(content, "in_progress")
    assert reverse("lead-detail", args=[lead.pk]) in segment
    assert "Itancan Consulting" in segment
    assert "100\xa0000 kr" in segment


@pytest.mark.django_db
def test_pipeline_board_sums_expected_value_per_stage(auth_client, company):
    for name in ["Java-utvecklare", ".NET-utvecklare"]:
        Lead.objects.create(
            name=name,
            company=company,
            expected_value=100000,
            stage=Lead.Stage.INTERVIEW,
        )
    # A missing value counts as a lead but adds nothing to the sum.
    Lead.objects.create(
        name="Projektledare", company=company, stage=Lead.Stage.INTERVIEW
    )
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "3 · 200\xa0000 kr" in column_segment(content, "interview")
    assert "0 · 0 kr" in column_segment(content, "quote")


@pytest.mark.django_db
def test_pipeline_board_has_drag_and_drop_hooks(auth_client, lead):
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "vendor/sortable.min.js" in content
    assert "js/pipeline.js" in content
    assert 'data-stage="in_progress"' in content
    assert f'data-stage-url="{reverse("lead-stage", args=[lead.pk])}"' in content
    assert 'data-stage-summary="quote"' in content


@pytest.mark.django_db
def test_stage_endpoint_moves_lead_and_returns_summaries(auth_client, lead):
    response = auth_client.post(
        reverse("lead-stage", args=[lead.pk]), {"stage": "quote"}
    )
    assert response.status_code == 200
    lead.refresh_from_db()
    assert lead.stage == Lead.Stage.QUOTE
    summaries = response.json()["summaries"]
    assert summaries["quote"] == "1 · 100\xa0000 kr"
    assert summaries["in_progress"] == "0 · 0 kr"
    assert set(summaries) == set(Lead.Stage.values)


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [{}, {"stage": "bogus"}])
def test_stage_endpoint_rejects_bad_stage(auth_client, lead, payload):
    response = auth_client.post(reverse("lead-stage", args=[lead.pk]), payload)
    assert response.status_code == 400
    lead.refresh_from_db()
    assert lead.stage == Lead.Stage.IN_PROGRESS


@pytest.mark.django_db
def test_stage_endpoint_requires_login(client, lead):
    response = client.post(reverse("lead-stage", args=[lead.pk]), {"stage": "quote"})
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    lead.refresh_from_db()
    assert lead.stage == Lead.Stage.IN_PROGRESS


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
def test_delete_lead_soft_deletes(auth_client, lead):
    response = auth_client.post(reverse("lead-delete", args=[lead.pk]))
    assert response.status_code == 302
    assert response.url == reverse("pipeline")
    lead.refresh_from_db()
    assert lead.deleted_at is not None


@pytest.mark.django_db
def test_deleted_lead_hidden_from_pipeline_and_summaries(auth_client, company):
    Lead.objects.create(
        name="Borttagen affär",
        company=company,
        expected_value=1000,
        deleted_at=timezone.now(),
    )
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert "Borttagen affär" not in content
    assert "0 · 0 kr" in column_segment(content, "in_progress")


@pytest.mark.django_db
def test_deleted_lead_detail_shows_banner_and_restore(auth_client, lead):
    lead.deleted_at = timezone.now()
    lead.save()
    response = auth_client.get(reverse("lead-detail", args=[lead.pk]))
    assert response.status_code == 200
    content = response.content.decode()
    assert "borttagen" in content
    assert reverse("lead-restore", args=[lead.pk]) in content


@pytest.mark.django_db
def test_active_lead_detail_has_no_restore(auth_client, lead):
    content = auth_client.get(reverse("lead-detail", args=[lead.pk])).content.decode()
    assert reverse("lead-restore", args=[lead.pk]) not in content


@pytest.mark.django_db
def test_restore_lead(auth_client, lead):
    lead.deleted_at = timezone.now()
    lead.save()
    response = auth_client.post(reverse("lead-restore", args=[lead.pk]))
    assert response.status_code == 302
    assert response.url == reverse("lead-detail", args=[lead.pk])
    lead.refresh_from_db()
    assert lead.deleted_at is None
    content = auth_client.get(reverse("pipeline")).content.decode()
    assert lead.name in content


@pytest.mark.django_db
def test_restore_requires_login(client, lead):
    lead.deleted_at = timezone.now()
    lead.save()
    response = client.post(reverse("lead-restore", args=[lead.pk]))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))
    lead.refresh_from_db()
    assert lead.deleted_at is not None


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
