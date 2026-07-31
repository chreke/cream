from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Candidate,
    CandidateComment,
    Company,
    CompanyComment,
    Contact,
    Lead,
    LeadComment,
    Resume,
    Tag,
    User,
)

admin.site.register(User, UserAdmin)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "industry", "assignee", "last_contacted"]
    list_filter = ["tags"]
    search_fields = ["name", "location"]
    filter_horizontal = ["tags"]
    inlines = [ContactInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "role", "email", "phone"]
    search_fields = ["name", "company__name"]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "location", "email", "flagged_by"]
    list_filter = ["kind"]
    search_fields = ["name", "location", "skills"]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["filename", "candidate", "uploaded_at"]
    search_fields = ["filename", "candidate__name"]


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "stage", "expected_value", "assignee", "deleted_at"]
    list_filter = ["stage"]
    search_fields = ["name", "company__name"]


@admin.register(CompanyComment)
class CompanyCommentAdmin(admin.ModelAdmin):
    list_display = ["company", "user", "created_at", "edited_at"]


@admin.register(CandidateComment)
class CandidateCommentAdmin(admin.ModelAdmin):
    list_display = ["candidate", "user", "created_at", "edited_at"]


@admin.register(LeadComment)
class LeadCommentAdmin(admin.ModelAdmin):
    list_display = ["lead", "user", "created_at", "edited_at"]
