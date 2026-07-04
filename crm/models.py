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
