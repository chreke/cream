import pytest
from django.urls import reverse

from crm.models import Candidate, CandidateComment, Company


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
def test_candidate_list_shows_total_candidate_count(auth_client):
    Candidate.objects.create(name="Sara Lind", kind=Candidate.Kind.FREELANCER)
    Candidate.objects.create(name="Erik Ek", kind=Candidate.Kind.EMPLOYEE)

    content = auth_client.get(
        reverse("candidate-list"), {"kind": "freelancer"}
    ).content.decode()

    assert "2 kandidater" in content


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
def test_candidate_list_search_combines_with_kind_and_location_filters(auth_client):
    Candidate.objects.create(
        name="Sara Lind",
        kind=Candidate.Kind.FREELANCER,
        location="Stockholm",
        skills="Java",
    )
    Candidate.objects.create(
        name="Erik Ek",
        kind=Candidate.Kind.EMPLOYEE,
        location="Stockholm",
        skills="Java",
    )
    Candidate.objects.create(
        name="Maria Malm",
        kind=Candidate.Kind.EMPLOYEE,
        location="Stockholm",
        skills="JavaScript",
    )
    Candidate.objects.create(
        name="Ove Olsson",
        kind=Candidate.Kind.EMPLOYEE,
        location="Göteborg",
        skills="Java",
    )
    response = auth_client.get(
        reverse("candidate-list"),
        {"q": "java", "kind": "employee", "location": "Stockholm"},
    )
    assert [c.name for c in response.context["candidates"]] == [
        "Erik Ek",
        "Maria Malm",
    ]

    # Blank query is ignored.
    response = auth_client.get(reverse("candidate-list"), {"q": "   "})
    assert len(response.context["candidates"]) == 4


@pytest.mark.django_db
def test_candidate_list_location_filter_is_exact_and_has_candidate_options(
    auth_client,
):
    Candidate.objects.create(
        name="Sara Lind", kind=Candidate.Kind.BOTH, location="Stockholm"
    )
    Candidate.objects.create(
        name="Erik Ek", kind=Candidate.Kind.BOTH, location="Stockholms län"
    )
    Candidate.objects.create(
        name="Anna Alm", kind=Candidate.Kind.BOTH, location="Göteborg"
    )
    Company.objects.create(name="Malmöbolaget", location="Malmö")

    response = auth_client.get(
        reverse("candidate-list"), {"location": "Stockholm"}
    )

    assert [candidate.name for candidate in response.context["candidates"]] == [
        "Sara Lind"
    ]
    assert response.context["current_location"] == "Stockholm"
    assert response.context["candidate_location_options"] == [
        "Göteborg",
        "Stockholm",
        "Stockholms län",
    ]
    content = response.content.decode()
    assert '<select name="location"' in content
    assert '<option value="Stockholm" selected>' in content


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
    # Only the flagged candidate's row gets the flag emoji.
    assert content.count("🚩") == 1


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
