from django.urls import path

from . import views

urlpatterns = [
    path("companies/", views.company_list, name="company-list"),
    path("candidates/", views.candidate_list, name="candidate-list"),
    path("pipeline/", views.pipeline, name="pipeline"),
]
