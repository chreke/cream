from django.urls import path

from . import views

urlpatterns = [
    path("companies/", views.CompanyListView.as_view(), name="company-list"),
    path("companies/new/", views.CompanyCreateView.as_view(), name="company-create"),
    path(
        "companies/<int:pk>/edit/",
        views.CompanyUpdateView.as_view(),
        name="company-edit",
    ),
    path("candidates/", views.CandidateListView.as_view(), name="candidate-list"),
    path("pipeline/", views.PipelineView.as_view(), name="pipeline"),
]
