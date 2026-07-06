from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Company(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    homepage = models.URLField(blank=True)
    organization_number = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)  # Markdown
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="companies",
    )
    last_contacted = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class Contact(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="contacts"
    )
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Candidate(models.Model):
    class Kind(models.TextChoices):
        FREELANCER = "freelancer", "Frilansare"
        EMPLOYEE = "employee", "Anställd"
        BOTH = "both", "Båda"

    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    location = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    linkedin_url = models.URLField(blank=True)
    description = models.TextField(blank=True)  # Markdown
    skills = models.TextField(blank=True)  # Comma-separated list
    flagged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="flagged_candidates",
    )
    flag_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BaseComment(models.Model):
    """Shared fields for comments; concrete subclasses add the target FK."""

    content = models.TextField()  # Markdown
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)ss",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="edited_%(class)ss",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class CompanyComment(BaseComment):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"Comment on {self.company} by {self.user}"
