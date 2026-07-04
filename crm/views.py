from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import CompanyForm
from .models import Company


class CompanyListView(ListView):
    model = Company
    context_object_name = "companies"
    paginate_by = 50
    extra_context = {"section": "companies"}

    def get_queryset(self):
        queryset = Company.objects.select_related("assignee")

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(location__icontains=query)
            )

        assignee = self.request.GET.get("assignee", "")
        if assignee.isdigit():
            queryset = queryset.filter(assignee=assignee)

        if self.request.GET.get("sort") == "last_contacted":
            # Never/least-recently contacted first: these companies need attention.
            queryset = queryset.order_by(
                F("last_contacted").asc(nulls_first=True), "name"
            )
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = get_user_model().objects.order_by("username")
        context["current_q"] = self.request.GET.get("q", "")
        context["current_assignee"] = self.request.GET.get("assignee", "")
        context["current_sort"] = self.request.GET.get("sort", "name")

        # Query string without "page", for pagination links.
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        # Query string without "page" and "sort", for sort header links.
        params.pop("sort", None)
        context["sort_querystring"] = params.urlencode()
        return context


class CompanyModalMixin:
    """Company modals render on top of the companies list as a backdrop.

    The backdrop shows the default first page of the list; search/filter
    state is not carried into modal URLs.
    """

    model = Company
    success_url = reverse_lazy("company-list")
    extra_context = {"section": "companies"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = (
            Company.objects.select_related("assignee").order_by("name")[:50]
        )
        context["users"] = get_user_model().objects.order_by("username")
        context["current_q"] = ""
        context["current_assignee"] = ""
        context["current_sort"] = "name"
        context["querystring"] = ""
        context["sort_querystring"] = ""
        return context


class CompanyCreateView(CompanyModalMixin, CreateView):
    form_class = CompanyForm


class CompanyUpdateView(CompanyModalMixin, UpdateView):
    form_class = CompanyForm


class CompanyDeleteView(CompanyModalMixin, DeleteView):
    pass


class CandidateListView(TemplateView):
    template_name = "crm/candidate_list.html"
    extra_context = {"section": "candidates"}


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
