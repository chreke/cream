from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Company, CompanyComment, Contact, User

admin.site.register(User, UserAdmin)


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "industry", "assignee", "last_contacted"]
    search_fields = ["name", "location"]
    inlines = [ContactInline]


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "role", "email", "phone"]
    search_fields = ["name", "company__name"]


@admin.register(CompanyComment)
class CompanyCommentAdmin(admin.ModelAdmin):
    list_display = ["company", "user", "created_at", "edited_at"]
