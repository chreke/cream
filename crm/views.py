from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import CommentForm, CompanyForm, ContactForm, LogContactForm
from .models import Company, CompanyComment, Contact


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

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.pk])


class CompanyDeleteView(CompanyModalMixin, DeleteView):
    pass


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"
    extra_context = {"section": "companies"}
    queryset = Company.objects.select_related("assignee").prefetch_related(
        "contacts", "comments__user", "comments__last_edited_by"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("comment_form", CommentForm())
        return context


class CompanyPageMixin:
    """Views rendered as a modal or inline form on top of a company detail page."""

    extra_context = {"section": "companies"}

    def get_company(self):
        return get_object_or_404(Company, pk=self.kwargs["company_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company"] = self.get_company()
        context.setdefault("comment_form", CommentForm())
        return context

    def get_success_url(self):
        return reverse("company-detail", args=[self.get_company().pk])


class ContactCreateView(CompanyPageMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"

    def form_valid(self, form):
        form.instance.company = self.get_company()
        return super().form_valid(form)


class ContactUpdateView(CompanyPageMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = "crm/contact_form.html"

    def get_company(self):
        return self.get_object().company


class ContactDeleteView(CompanyPageMixin, DeleteView):
    model = Contact

    def get_company(self):
        return self.get_object().company


class LogContactView(CompanyPageMixin, FormView):
    form_class = LogContactForm
    template_name = "crm/log_contact.html"

    def form_valid(self, form):
        company = self.get_company()
        company.last_contacted = timezone.now()
        company.save()
        if form.cleaned_data["comment"]:
            CompanyComment.objects.create(
                company=company,
                user=self.request.user,
                content=form.cleaned_data["comment"],
            )
        return super().form_valid(form)


class CompanyCommentCreateView(CompanyPageMixin, CreateView):
    model = CompanyComment
    form_class = CommentForm
    template_name = "crm/company_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.company = self.get_company()
        form.instance.user = self.request.user
        return super().form_valid(form)


class CompanyCommentUpdateView(CompanyPageMixin, UpdateView):
    model = CompanyComment
    form_class = CommentForm
    template_name = "crm/company_detail.html"

    def get_company(self):
        return self.get_object().company

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["editing_comment"] = self.object
        context["comment_edit_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.edited_at = timezone.now()
        form.instance.last_edited_by = self.request.user
        return super().form_valid(form)


class CompanyCommentDeleteView(CompanyPageMixin, DeleteView):
    model = CompanyComment
    template_name = "crm/companycomment_confirm_delete.html"

    def get_company(self):
        return self.get_object().company


class CandidateListView(TemplateView):
    template_name = "crm/candidate_list.html"
    extra_context = {"section": "candidates"}


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
