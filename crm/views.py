from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect
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


def company_list_context():
    """Context needed to render the companies list page as a modal host."""
    return {
        "companies": Company.objects.select_related("assignee").order_by("name")[:50],
        "users": get_user_model().objects.order_by("username"),
        "current_q": "",
        "current_assignee": "",
        "current_sort": "name",
        "querystring": "",
        "sort_querystring": "",
    }


def company_detail_context(company):
    """Context needed to render the company detail page and its modals.

    Pages embed several forms at once, so each form gets its own auto_id
    prefix to keep field ids unique.
    """
    return {
        "company": company,
        "company_form": CompanyForm(instance=company, auto_id="company-edit-%s"),
        "log_contact_form": LogContactForm(auto_id="log-contact-%s"),
        "contact_create_form": ContactForm(auto_id="contact-new-%s"),
        "contact_items": [
            (contact, ContactForm(instance=contact, auto_id=f"contact-{contact.pk}-%s"))
            for contact in company.contacts.all()
        ],
        "comment_form": CommentForm(auto_id="comment-new-%s"),
        "comment_items": [
            (comment, CommentForm(instance=comment, auto_id=f"comment-{comment.pk}-%s"))
            for comment in company.comments.all()
        ],
    }


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
        context["company_create_form"] = CompanyForm(auto_id="company-new-%s")

        # Query string without "page", for pagination links.
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        # Query string without "page" and "sort", for sort header links.
        params.pop("sort", None)
        context["sort_querystring"] = params.urlencode()
        return context


class CompanyDetailView(DetailView):
    model = Company
    context_object_name = "company"
    extra_context = {"section": "companies"}
    queryset = Company.objects.select_related("assignee").prefetch_related(
        "contacts", "comments__user", "comments__last_edited_by"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(company_detail_context(self.object))
        return context


class CompanyCreateView(CreateView):
    """POST target for the create modal on the companies list page."""

    model = Company
    form_class = CompanyForm
    template_name = "crm/company_list.html"
    success_url = reverse_lazy("company-list")
    extra_context = {"section": "companies"}

    def get(self, request, *args, **kwargs):
        return redirect("company-list")

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"auto_id": "company-new-%s"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for key, value in company_list_context().items():
            context.setdefault(key, value)
        context["company_create_form"] = context["form"]
        context["open_modal"] = "company-create-modal"
        return context


class CompanyDetailHostedMixin:
    """Endpoints whose modal lives on the company detail page.

    Needed for displaying validation errors without JavaScript: modals
    have no page of their own, so an invalid POST re-renders the full
    detail page with the failing modal reopened via `open_modal` and the
    form's errors shown inside it. GET redirects to the detail page.
    """

    template_name = "crm/company_detail.html"
    extra_context = {"section": "companies"}
    open_modal = None

    def get_company(self):
        return get_object_or_404(Company, pk=self.kwargs["company_pk"])

    def get(self, request, *args, **kwargs):
        return redirect("company-detail", pk=self.get_company().pk)

    def get_success_url(self):
        return reverse("company-detail", args=[self.get_company().pk])

    def get_open_modal(self):
        return self.open_modal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for key, value in company_detail_context(self.get_company()).items():
            context.setdefault(key, value)
        context["open_modal"] = self.get_open_modal()
        return context


class CompanyUpdateView(CompanyDetailHostedMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    open_modal = "company-edit-modal"

    def get_company(self):
        return self.get_object()

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"auto_id": "company-edit-%s"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["company_form"] = context["form"]
        return context


class CompanyDeleteView(DeleteView):
    """POST target for the delete-confirmation modal on the detail page."""

    model = Company
    success_url = reverse_lazy("company-list")

    def get(self, request, *args, **kwargs):
        return redirect("company-detail", pk=self.get_object().pk)


class ContactCreateView(CompanyDetailHostedMixin, CreateView):
    model = Contact
    form_class = ContactForm
    open_modal = "contact-create-modal"

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"auto_id": "contact-new-%s"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_create_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.company = self.get_company()
        return super().form_valid(form)


class ContactUpdateView(CompanyDetailHostedMixin, UpdateView):
    model = Contact
    form_class = ContactForm

    def get_company(self):
        return self.get_object().company

    def get_open_modal(self):
        return f"contact-edit-modal-{self.kwargs['pk']}"

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "auto_id": f"contact-{self.kwargs['pk']}-%s"
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_items"] = [
            (contact, context["form"] if contact.pk == self.object.pk else form)
            for contact, form in context["contact_items"]
        ]
        return context


class ContactDeleteView(CompanyDetailHostedMixin, DeleteView):
    model = Contact

    def get_company(self):
        return self.get_object().company


class LogContactView(CompanyDetailHostedMixin, FormView):
    form_class = LogContactForm
    open_modal = "log-contact-modal"

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


class CompanyCommentCreateView(CompanyDetailHostedMixin, CreateView):
    """POST target for the inline new-comment form on the detail page."""

    model = CompanyComment
    form_class = CommentForm

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"auto_id": "comment-new-%s"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.company = self.get_company()
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return f"{super().get_success_url()}#comment-{self.object.pk}"


class CompanyCommentUpdateView(CompanyDetailHostedMixin, UpdateView):
    model = CompanyComment
    form_class = CommentForm

    def get_company(self):
        return self.get_object().company

    def get_open_modal(self):
        return f"comment-edit-modal-{self.kwargs['pk']}"

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {
            "auto_id": f"comment-{self.kwargs['pk']}-%s"
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_items"] = [
            (comment, context["form"] if comment.pk == self.object.pk else form)
            for comment, form in context["comment_items"]
        ]
        return context

    def form_valid(self, form):
        form.instance.edited_at = timezone.now()
        form.instance.last_edited_by = self.request.user
        return super().form_valid(form)


class CompanyCommentDeleteView(CompanyDetailHostedMixin, DeleteView):
    model = CompanyComment

    def get_company(self):
        return self.get_object().company


class CandidateListView(TemplateView):
    template_name = "crm/candidate_list.html"
    extra_context = {"section": "candidates"}


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
