from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Company, User

admin.site.register(User, UserAdmin)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "industry", "assignee", "last_contacted"]
    search_fields = ["name", "location"]
