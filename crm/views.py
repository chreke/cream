from django.views.generic import TemplateView


class CompanyListView(TemplateView):
    template_name = "crm/company_list.html"
    extra_context = {"section": "companies"}


class CandidateListView(TemplateView):
    template_name = "crm/candidate_list.html"
    extra_context = {"section": "candidates"}


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
