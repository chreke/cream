from django.urls import path

from . import views

urlpatterns = [
    path("companies/", views.CompanyListView.as_view(), name="company-list"),
    path("candidates/", views.CandidateListView.as_view(), name="candidate-list"),
    path("pipeline/", views.PipelineView.as_view(), name="pipeline"),
]
