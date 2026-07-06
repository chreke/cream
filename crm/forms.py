from django import forms

from .models import Candidate, Company, CompanyComment, Contact


class CompanyForm(forms.ModelForm):
    homepage = forms.URLField(
        label="Hemsida",
        required=False,
        assume_scheme="https",
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
                attrs={"class": "form-control", "list": "location-options"}
            ),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "homepage": forms.URLInput(attrs={"class": "form-control"}),
            "organization_number": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
        }


class CandidateForm(forms.ModelForm):
    linkedin_url = forms.URLField(
        label="LinkedIn",
        required=False,
        assume_scheme="https",
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
                attrs={"class": "form-control", "list": "location-options"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }


class ContactForm(forms.ModelForm):
    linkedin_url = forms.URLField(
        label="LinkedIn",
        required=False,
        assume_scheme="https",
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


class CommentForm(forms.ModelForm):
    class Meta:
        model = CompanyComment
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


class LogContactForm(forms.Form):
    comment = forms.CharField(
        label="Kommentar (valfritt)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
