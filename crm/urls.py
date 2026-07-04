from django.urls import path

from . import views

urlpatterns = [
    path("companies/", views.CompanyListView.as_view(), name="company-list"),
    path("companies/new/", views.CompanyCreateView.as_view(), name="company-create"),
    path(
        "companies/<int:pk>/",
        views.CompanyDetailView.as_view(),
        name="company-detail",
    ),
    path(
        "companies/<int:pk>/edit/",
        views.CompanyUpdateView.as_view(),
        name="company-edit",
    ),
    path(
        "companies/<int:pk>/delete/",
        views.CompanyDeleteView.as_view(),
        name="company-delete",
    ),
    path(
        "companies/<int:company_pk>/log-contact/",
        views.LogContactView.as_view(),
        name="company-log-contact",
    ),
    path(
        "companies/<int:company_pk>/contacts/new/",
        views.ContactCreateView.as_view(),
        name="contact-create",
    ),
    path(
        "contacts/<int:pk>/edit/",
        views.ContactUpdateView.as_view(),
        name="contact-edit",
    ),
    path(
        "contacts/<int:pk>/delete/",
        views.ContactDeleteView.as_view(),
        name="contact-delete",
    ),
    path(
        "companies/<int:company_pk>/comments/new/",
        views.CompanyCommentCreateView.as_view(),
        name="company-comment-create",
    ),
    path(
        "company-comments/<int:pk>/edit/",
        views.CompanyCommentUpdateView.as_view(),
        name="company-comment-edit",
    ),
    path(
        "company-comments/<int:pk>/delete/",
        views.CompanyCommentDeleteView.as_view(),
        name="company-comment-delete",
    ),
    path("candidates/", views.CandidateListView.as_view(), name="candidate-list"),
    path("pipeline/", views.PipelineView.as_view(), name="pipeline"),
]
