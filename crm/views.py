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


def company_list_context():
    """Context needed to render the companies list page as a modal host."""
    return {
        "location_options": location_options(),
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


class AutoIdFormMixin:
    """Gives the view's form a distinct `auto_id` prefix.

    Pages here embed several forms at once (create modal, edit modals,
    comment forms...), so default `id_<field>` ids would collide across
    forms. Set `form_auto_id` to a prefix like "company-edit-%s", or
    override `get_form_auto_id()` when the prefix depends on the URL
    (e.g. one edit form per object on the page).
    """

    form_auto_id = None

    def get_form_auto_id(self):
        return self.form_auto_id

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"auto_id": self.get_form_auto_id()}


class DetailHostedMixin:
    """Base for endpoints whose form lives in a modal on a detail page.

    This app has no standalone form pages: objects are created, edited
    and deleted through Bootstrap modals embedded in a host object's
    detail page (see the UI section of REQUIREMENTS.md), and plain
    Create/Update/DeleteView subclasses serve as the POST targets for
    those modals. This mixin adapts them to that setup:

    - GET redirects to the host's detail page (the endpoint has no page
      of its own; the modal markup is already there).
    - A successful POST redirects back to the host's detail page.
    - An invalid POST re-renders the *complete* detail page around the
      bound form, with the failing modal reopened via the `open_modal`
      context variable (a script in base.html opens it on load), so the
      validation errors show up inside the modal. This keeps validation
      server-side with no JavaScript beyond Bootstrap itself.

    A subclass per host model provides the page specifics:

    - `template_name` / `extra_context`: the detail page and nav section
    - `detail_url_name`: url name of the detail page (takes the host pk)
    - `get_host_object()`: the object whose detail page hosts the modal
    - `get_detail_context(host)`: everything the page needs to render;
      merged with `setdefault` so the view's own bound form wins

    Views on top of that set `open_modal` to the id of their modal (or
    override `get_open_modal()` when the id depends on the URL), and
    override `get_host_object()` when the host is reached through the
    edited object (e.g. `self.get_object().company`).
    """

    detail_url_name = None
    open_modal = None

    def get_host_object(self):
        raise NotImplementedError

    def get_detail_context(self, host):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        return redirect(self.detail_url_name, pk=self.get_host_object().pk)

    def get_success_url(self):
        return reverse(self.detail_url_name, args=[self.get_host_object().pk])

    def get_open_modal(self):
        return self.open_modal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for key, value in self.get_detail_context(self.get_host_object()).items():
            context.setdefault(key, value)
        context["open_modal"] = self.get_open_modal()
        return context


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


class CompanyCreateView(AutoIdFormMixin, CreateView):
    """POST target for the create modal on the companies list page."""

    model = Company
    form_class = CompanyForm
    template_name = "crm/company_list.html"
    success_url = reverse_lazy("company-list")
    extra_context = {"section": "companies"}
    form_auto_id = "company-new-%s"

    def get(self, request, *args, **kwargs):
        return redirect("company-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for key, value in company_list_context().items():
            context.setdefault(key, value)
        context["company_create_form"] = context["form"]
        context["open_modal"] = "company-create-modal"
        return context


class CompanyDetailHostedMixin(DetailHostedMixin):
    template_name = "crm/company_detail.html"
    extra_context = {"section": "companies"}
    detail_url_name = "company-detail"

    def get_host_object(self):
        return get_object_or_404(Company, pk=self.kwargs["company_pk"])

    def get_detail_context(self, company):
        return company_detail_context(company)


class CompanyUpdateView(AutoIdFormMixin, CompanyDetailHostedMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    open_modal = "company-edit-modal"
    form_auto_id = "company-edit-%s"

    def get_host_object(self):
        return self.get_object()

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


class ContactCreateView(AutoIdFormMixin, CompanyDetailHostedMixin, CreateView):
    model = Contact
    form_class = ContactForm
    open_modal = "contact-create-modal"
    form_auto_id = "contact-new-%s"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_create_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.company = self.get_host_object()
        return super().form_valid(form)


class ContactUpdateView(AutoIdFormMixin, CompanyDetailHostedMixin, UpdateView):
    model = Contact
    form_class = ContactForm

    def get_host_object(self):
        return self.get_object().company

    def get_open_modal(self):
        return f"contact-edit-modal-{self.kwargs['pk']}"

    def get_form_auto_id(self):
        return f"contact-{self.kwargs['pk']}-%s"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contact_items"] = [
            (contact, context["form"] if contact.pk == self.object.pk else form)
            for contact, form in context["contact_items"]
        ]
        return context


class ContactDeleteView(CompanyDetailHostedMixin, DeleteView):
    model = Contact

    def get_host_object(self):
        return self.get_object().company


class LogContactView(CompanyDetailHostedMixin, FormView):
    form_class = LogContactForm
    open_modal = "log-contact-modal"

    def form_valid(self, form):
        company = self.get_host_object()
        company.last_contacted = timezone.now()
        company.save()
        if form.cleaned_data["comment"]:
            CompanyComment.objects.create(
                company=company,
                user=self.request.user,
                content=form.cleaned_data["comment"],
            )
        return super().form_valid(form)


class CompanyCommentCreateView(AutoIdFormMixin, CompanyDetailHostedMixin, CreateView):
    """POST target for the inline new-comment form on the detail page."""

    model = CompanyComment
    form_class = CompanyCommentForm
    form_auto_id = "comment-new-%s"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.company = self.get_host_object()
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return f"{super().get_success_url()}#comment-{self.object.pk}"


class CompanyCommentUpdateView(AutoIdFormMixin, CompanyDetailHostedMixin, UpdateView):
    model = CompanyComment
    form_class = CompanyCommentForm

    def get_host_object(self):
        return self.get_object().company

    def get_open_modal(self):
        return f"comment-edit-modal-{self.kwargs['pk']}"

    def get_form_auto_id(self):
        return f"comment-{self.kwargs['pk']}-%s"

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

    def get_host_object(self):
        return self.get_object().company


def candidate_list_context():
    """Context needed to render the candidates list page as a modal host."""
    return {
        "candidates": Candidate.objects.all()[:50],
        "location_options": location_options(),
        "current_q": "",
        "current_kind": "",
        "querystring": "",
    }


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


class CandidateCreateView(AutoIdFormMixin, CreateView):
    """POST target for the create modal on the candidates list page."""

    model = Candidate
    form_class = CandidateForm
    template_name = "crm/candidate_list.html"
    extra_context = {"section": "candidates"}
    form_auto_id = "candidate-new-%s"

    def get(self, request, *args, **kwargs):
        return redirect("candidate-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for key, value in candidate_list_context().items():
            context.setdefault(key, value)
        context["candidate_create_form"] = context["form"]
        context["open_modal"] = "candidate-create-modal"
        return context

    def get_success_url(self):
        return reverse("candidate-detail", args=[self.object.pk])


class CandidateDetailHostedMixin(DetailHostedMixin):
    template_name = "crm/candidate_detail.html"
    extra_context = {"section": "candidates"}
    detail_url_name = "candidate-detail"

    def get_host_object(self):
        return self.get_object()

    def get_detail_context(self, candidate):
        return candidate_detail_context(candidate)


class CandidateUpdateView(AutoIdFormMixin, CandidateDetailHostedMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm
    open_modal = "candidate-edit-modal"
    form_auto_id = "candidate-edit-%s"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["candidate_form"] = context["form"]
        return context


class CandidateDeleteView(CandidateDetailHostedMixin, DeleteView):
    model = Candidate

    def get_success_url(self):
        return reverse("candidate-list")


class CandidateCommentCreateView(
    AutoIdFormMixin, CandidateDetailHostedMixin, CreateView
):
    """POST target for the inline new-comment form on the detail page."""

    model = CandidateComment
    form_class = CandidateCommentForm
    form_auto_id = "comment-new-%s"

    def get_host_object(self):
        return get_object_or_404(Candidate, pk=self.kwargs["candidate_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = context["form"]
        return context

    def form_valid(self, form):
        form.instance.candidate = self.get_host_object()
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return f"{super().get_success_url()}#comment-{self.object.pk}"


class CandidateCommentUpdateView(
    AutoIdFormMixin, CandidateDetailHostedMixin, UpdateView
):
    model = CandidateComment
    form_class = CandidateCommentForm

    def get_host_object(self):
        return self.get_object().candidate

    def get_open_modal(self):
        return f"comment-edit-modal-{self.kwargs['pk']}"

    def get_form_auto_id(self):
        return f"comment-{self.kwargs['pk']}-%s"

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


class CandidateCommentDeleteView(CandidateDetailHostedMixin, DeleteView):
    model = CandidateComment

    def get_host_object(self):
        return self.get_object().candidate


class PipelineView(TemplateView):
    template_name = "crm/pipeline.html"
    extra_context = {"section": "pipeline"}
