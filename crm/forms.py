from django import forms

from .models import Company


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
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "homepage": forms.URLInput(attrs={"class": "form-control"}),
            "organization_number": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "assignee": forms.Select(attrs={"class": "form-select"}),
        }
