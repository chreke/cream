from django import forms
from django.db import IntegrityError, transaction

from .models import (
    Candidate,
    CandidateComment,
    Company,
    CompanyComment,
    Contact,
    Lead,
    LeadComment,
    Tag,
)


class TagNamesField(forms.MultipleChoiceField):
    """An open multiple-choice field: Tom Select may submit new names."""

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(
                self.error_messages["required"], code="required"
            )


class CompanyForm(forms.ModelForm):
    tag_names = TagNamesField(
        label="Taggar",
        required=False,
        choices=(),
        widget=forms.SelectMultiple(
            attrs={"class": "form-select", "data-tag-input": ""}
        ),
    )
    homepage = forms.URLField(
        label="Hemsida",
        required=False,
        assume_scheme="https",  # pyright: ignore[reportCallIssue]  (missing from django-types)
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Company
        fields = [
            "name",
            "location",
            "industry",
            "homepage",
            "organization_number",
            "description",
            "assignee",
        ]
        labels = {
            "name": "Namn",
            "location": "Plats",
            "industry": "Bransch",
            "homepage": "Hemsida",
            "organization_number": "Organisationsnummer",
            "description": "Beskrivning",
            "assignee": "Ansvarig",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(
                attrs={"class": "form-control", "data-location-input": ""}
            ),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "homepage": forms.URLInput(attrs={"class": "form-control"}),
            "organization_number": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tag_names"].choices = [
            (tag.name, tag.name) for tag in Tag.objects.all()
        ]
        if self.instance.pk:
            self.initial["tag_names"] = list(
                self.instance.tags.values_list("name", flat=True)
            )

    def clean_tag_names(self):
        names = []
        seen = set()
        max_length = Tag._meta.get_field("name").max_length
        for raw_name in self.cleaned_data["tag_names"]:
            name = raw_name.strip()
            if not name:
                continue
            if len(name) > max_length:
                raise forms.ValidationError(
                    f"Taggar får vara högst {max_length} tecken långa."
                )
            key = name.casefold()
            if key not in seen:
                seen.add(key)
                names.append(name)
        return names

    def save(self, commit=True):
        company = super().save(commit=commit)
        if commit:
            self._save_tags()
        else:
            original_save_m2m = self.save_m2m

            def save_m2m():
                original_save_m2m()
                self._save_tags()

            self.save_m2m = save_m2m
        return company

    def _save_tags(self):
        tags = [
            self._get_or_create_tag(name)
            for name in self.cleaned_data["tag_names"]
        ]
        self.instance.tags.set(tags)

    @staticmethod
    def _get_or_create_tag(name):
        tag = Tag.objects.filter(name__iexact=name).first()
        if tag is not None:
            return tag

        # The database constraint is the final guard against two users
        # concurrently creating differently-cased versions of the same tag.
        try:
            with transaction.atomic():
                return Tag.objects.create(name=name)
        except IntegrityError:
            return Tag.objects.get(name__iexact=name)


class CandidateForm(forms.ModelForm):
    linkedin_url = forms.URLField(
        label="LinkedIn",
        required=False,
        assume_scheme="https",  # pyright: ignore[reportCallIssue]  (missing from django-types)
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Candidate
        fields = [
            "name",
            "kind",
            "location",
            "email",
            "phone",
            "linkedin_url",
            "skills",
            "description",
        ]
        labels = {
            "name": "Namn",
            "kind": "Typ",
            "location": "Plats",
            "email": "E-post",
            "phone": "Telefon",
            "skills": "Kompetenser (kommaseparerade)",
            "description": "Beskrivning",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(
                attrs={"class": "form-control", "data-location-input": ""}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }


class CandidateFlagForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["flag_reason"]
        labels = {"flag_reason": "Anledning (valfritt)"}
        widgets = {
            "flag_reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ContactForm(forms.ModelForm):
    linkedin_url = forms.URLField(
        label="LinkedIn",
        required=False,
        assume_scheme="https",  # pyright: ignore[reportCallIssue]  (missing from django-types)
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Contact
        fields = ["name", "role", "linkedin_url", "email", "phone"]
        labels = {
            "name": "Namn",
            "role": "Roll",
            "email": "E-post",
            "phone": "Telefon",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class LeadCreateForm(forms.ModelForm):
    """New leads pick a company but no contact or stage; the contact is
    set from the edit modal (where the company is known) and the stage
    always starts at Pågående."""

    class Meta:
        model = Lead
        fields = ["name", "company", "expected_value", "assignee"]
        labels = {
            "name": "Namn",
            "company": "Företag",
            "expected_value": "Förväntat värde (kr)",
            "assignee": "Ansvarig",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.Select(attrs={"class": "form-select"}),
            "expected_value": forms.NumberInput(attrs={"class": "form-control"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
        }


class LeadEditForm(forms.ModelForm):
    """The company is fixed after creation; the contact dropdown only
    offers the lead's own company's contacts."""

    class Meta:
        model = Lead
        fields = ["name", "expected_value", "contact", "assignee", "stage"]
        labels = {
            "name": "Namn",
            "expected_value": "Förväntat värde (kr)",
            "contact": "Kontakt",
            "assignee": "Ansvarig",
            "stage": "Fas",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "expected_value": forms.NumberInput(attrs={"class": "form-control"}),
            "contact": forms.Select(attrs={"class": "form-select"}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
            "stage": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contact"].queryset = self.instance.company.contacts.all()


class BaseCommentForm(forms.ModelForm):
    """Shared comment form; concrete subclasses set the comment model."""

    class Meta:
        fields = ["content"]
        labels = {"content": "Kommentar"}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Skriv en kommentar...",
                }
            ),
        }


class CompanyCommentForm(BaseCommentForm):
    class Meta(BaseCommentForm.Meta):
        model = CompanyComment


class CandidateCommentForm(BaseCommentForm):
    class Meta(BaseCommentForm.Meta):
        model = CandidateComment


class LeadCommentForm(BaseCommentForm):
    class Meta(BaseCommentForm.Meta):
        model = LeadComment


class ResumeForm(forms.Form):
    MAX_SIZE = 20 * 1024 * 1024  # 20 MB

    file = forms.FileField(
        label="Fil",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )

    def clean_file(self):
        file = self.cleaned_data["file"]
        if file.size > self.MAX_SIZE:
            raise forms.ValidationError("Filen är för stor (max 20 MB).")
        return file


class LogContactForm(forms.Form):
    comment = forms.CharField(
        label="Kommentar (valfritt)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
