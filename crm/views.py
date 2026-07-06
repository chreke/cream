from django.contrib import messages
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

from .forms import (
    CandidateForm,
    CandidateCommentForm,
    CompanyCommentForm,
    CompanyForm,
    ContactForm,
    LogContactForm,
)
from .models import Candidate, CandidateComment, Company, CompanyComment, Contact


def location_options():
    """Existing locations, suggested by the location-input <datalist>."""
    return sorted(
        set(Company.objects.exclude(location="").values_list("location", flat=True))
        | set(
            Candidate.objects.exclude(location="").values_list("location", flat=True)
        ),
        key=str.casefold,
    )


def company_detail_context(company):
    """Context needed to render the company detail page and its modals.

    Pages embed several forms at once, so each form gets its own auto_id
    prefix to keep field ids unique.
    """
    return {
        "company": company,
        "location_options": location_options(),
        "company_form": CompanyForm(instance=company, auto_id="company-edit-%s"),
        "log_contact_form": LogContactForm(auto_id="log-contact-%s"),
        "contact_create_form": ContactForm(auto_id="contact-new-%s"),
        "contact_items": [
            (contact, ContactForm(instance=contact, auto_id=f"contact-{contact.pk}-%s"))
            for contact in company.contacts.all()
        ],
        "comment_form": CompanyCommentForm(auto_id="comment-new-%s"),
        "comment_items": [
            (comment, CompanyCommentForm(instance=comment, auto_id=f"comment-{comment.pk}-%s"))
            for comment in company.comments.all()
        ],
    }


class FlashFormErrorsMixin:
    """POST-only endpoint behind a modal: on a failed form submission,
    flash the errors and redirect instead of re-rendering the page.

    Forms live in Bootstrap modals embedded in the page that links to
    them (see the UI section of REQUIREMENTS.md), so these endpoints
    have no page of their own. Client-side validation (`required`,
    `type="email"`/`"url"`, ...) catches nearly all bad input before it
    reaches the server, so we don't optimize for displaying server-side
    errors: a rejected POST redirects back with the errors as flash
    messages (rendered in base.html), and the submitted values are
    lost. GET requests (stale bookmarks, back button) also redirect.

    Views define `get_failure_url()` — where to land after a failed
    POST or a GET. It is separate from `get_success_url()` because a
    create view has no created object to build its success URL from
    when validation fails.
    """

    def get(self, request, *args, **kwargs):
        return redirect(self.get_failure_url())

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            label = form.fields[field].label if field in form.fields else None
            for error in errors:
                messages.error(
                    self.request, f"{label}: {error}" if label else error
                )
        return redirect(self.get_failure_url())


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
        context["location_options"] = location_options()

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


class CompanyCreateView(FlashFormErrorsMixin, CreateView):
    """POST target for the create modal on the companies list page."""

    model = Company
    form_class = CompanyForm
    success_url = reverse_lazy("company-list")

    def get_failure_url(self):
        return reverse("company-list")


class CompanyUpdateView(FlashFormErrorsMixin, UpdateView):
    model = Company
    form_class = CompanyForm

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.pk])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.kwargs["pk"]])


class CompanyDeleteView(FlashFormErrorsMixin, DeleteView):
    """POST target for the delete-confirmation modal on the detail page."""

    model = Company
    success_url = reverse_lazy("company-list")

    def get_failure_url(self):
        return reverse("company-detail", args=[self.kwargs["pk"]])


class ContactCreateView(FlashFormErrorsMixin, CreateView):
    model = Contact
    form_class = ContactForm

    def form_valid(self, form):
        form.instance.company = get_object_or_404(
            Company, pk=self.kwargs["company_pk"]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("company-detail", args=[self.kwargs["company_pk"]])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.kwargs["company_pk"]])


class ContactUpdateView(FlashFormErrorsMixin, UpdateView):
    model = Contact
    form_class = ContactForm

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.company_id])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.get_object().company_id])


class ContactDeleteView(FlashFormErrorsMixin, DeleteView):
    model = Contact

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.company_id])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.get_object().company_id])


class LogContactView(FlashFormErrorsMixin, FormView):
    form_class = LogContactForm

    def form_valid(self, form):
        company = get_object_or_404(Company, pk=self.kwargs["company_pk"])
        company.last_contacted = timezone.now()
        company.save()
        if form.cleaned_data["comment"]:
            CompanyComment.objects.create(
                company=company,
                user=self.request.user,
                content=form.cleaned_data["comment"],
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("company-detail", args=[self.kwargs["company_pk"]])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.kwargs["company_pk"]])


class CompanyCommentCreateView(FlashFormErrorsMixin, CreateView):
    """POST target for the inline new-comment form on the detail page."""

    model = CompanyComment
    form_class = CompanyCommentForm

    def form_valid(self, form):
        form.instance.company = get_object_or_404(
            Company, pk=self.kwargs["company_pk"]
        )
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        detail_url = reverse("company-detail", args=[self.kwargs["company_pk"]])
        return f"{detail_url}#comment-{self.object.pk}"

    def get_failure_url(self):
        return reverse("company-detail", args=[self.kwargs["company_pk"]])


class CompanyCommentUpdateView(FlashFormErrorsMixin, UpdateView):
    model = CompanyComment
    form_class = CompanyCommentForm

    def form_valid(self, form):
        form.instance.edited_at = timezone.now()
        form.instance.last_edited_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.company_id])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.get_object().company_id])


class CompanyCommentDeleteView(FlashFormErrorsMixin, DeleteView):
    model = CompanyComment

    def get_success_url(self):
        return reverse("company-detail", args=[self.object.company_id])

    def get_failure_url(self):
        return reverse("company-detail", args=[self.get_object().company_id])


def candidate_detail_context(candidate):
    """Context needed to render the candidate detail page and its modals."""
    return {
        "candidate": candidate,
        "location_options": location_options(),
        "candidate_form": CandidateForm(
            instance=candidate, auto_id="candidate-edit-%s"
        ),
        "comment_form": CandidateCommentForm(auto_id="comment-new-%s"),
        "comment_items": [
            (
                comment,
                CandidateCommentForm(
                    instance=comment, auto_id=f"comment-{comment.pk}-%s"
                ),
            )
            for comment in candidate.comments.all()
        ],
    }


class CandidateListView(ListView):
    model = Candidate
    context_object_name = "candidates"
    paginate_by = 50
    extra_context = {"section": "candidates"}

    def get_queryset(self):
        queryset = Candidate.objects.all()

        kind = self.request.GET.get("kind", "")
        if kind in (Candidate.Kind.FREELANCER, Candidate.Kind.EMPLOYEE):
            # "Both" candidates match either kind, so they always show.
            queryset = queryset.filter(kind__in=[kind, Candidate.Kind.BOTH])

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.search(query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_kind"] = self.request.GET.get("kind", "")
        context["current_q"] = self.request.GET.get("q", "")

        # Query string without "page", for pagination links.
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()

        context["candidate_create_form"] = CandidateForm(auto_id="candidate-new-%s")
        context["location_options"] = location_options()
        return context


class CandidateDetailView(DetailView):
    model = Candidate
    context_object_name = "candidate"
    extra_context = {"section": "candidates"}
    queryset = Candidate.objects.prefetch_related(
        "comments__user", "comments__last_edited_by"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(candidate_detail_context(self.object))
        return context


class CandidateCreateView(FlashFormErrorsMixin, CreateView):
    """POST target for the create modal on the candidates list page."""

    model = Candidate
    form_class = CandidateForm

    def get_success_url(self):
        return reverse("candidate-detail", args=[self.object.pk])

    def get_failure_url(self):
        return reverse("candidate-list")


class CandidateUpdateView(FlashFormErrorsMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm

    def get_success_url(self):
        return reverse("candidate-detail", args=[self.object.pk])

    def get_failure_url(self):
        return reverse("candidate-detail", args=[self.kwargs["pk"]])


class CandidateDeleteView(FlashFormErrorsMixin, DeleteView):
    model = Candidate
    success_url = reverse_lazy("candidate-list")

    def get_failure_url(self):
        return reverse("candidate-detail", args=[self.kwargs["pk"]])


class CandidateCommentCreateView(FlashFormErrorsMixin, CreateView):
    """POST target for the inline new-comment form on the detail page."""

    model = CandidateComment
    form_class = CandidateCommentForm

    def form_valid(self, form):
        form.instance.candidate = get_object_or_404(
            Candidate, pk=self.kwargs["candidate_pk"]
        )
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        detail_url = reverse("candidate-detail", args=[self.kwargs["candidate_pk"]])
        return f"{detail_url}#comment-{self.object.pk}"

    def get_failure_url(self):
        return reverse("candidate-detail", args=[self.kwargs["candidate_pk"]])


class CandidateCommentUpdateView(FlashFormErrorsMixin, UpdateView):
    model = CandidateComment
    form_class = CandidateCommentForm

    def form_valid(self, form):
        form.instance.edited_at = timezone.now()
        form.instance.last_edited_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("candidate-detail", args=[self.object.candidate_id])

    def get_failure_url(self):
        return reverse("candidate-detail", args=[self.get_object().candidate_id])


class CandidateCommentDeleteView(FlashFormErrorsMixin, DeleteView):
    model = CandidateComment

    def get_success_url(self):
        return reverse("candidate-detail", args=[self.object.candidate_id])

    def get_failure_url(self):
        return reverse("candidate-detail", args=[self.get_object().candidate_id])


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
