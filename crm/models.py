from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models

# "simple" config: no stemming or stop words; skills, names and places
# should match literally. Must stay identical to the GinIndex expression
# in Candidate.Meta for searches to use the index.
CANDIDATE_SEARCH_VECTOR = SearchVector("name", "location", "skills", config="simple")


class User(AbstractUser):
    pass


class Company(models.Model):
    name = models.CharField(max_length=255, db_collation="sv-SE-x-icu")
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
    name = models.CharField(max_length=255, db_collation="sv-SE-x-icu")
    role = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CandidateQuerySet(models.QuerySet):
    def search(self, query):
        """Whole-word search over name/location/skills, most relevant first.

        See specs/006-candidate-search.md: all words must match (AND),
        no prefix/substring matching, ties broken by name.
        """
        search_query = SearchQuery(query, config="simple")
        return (
            self.annotate(
                search=CANDIDATE_SEARCH_VECTOR,
                rank=SearchRank(CANDIDATE_SEARCH_VECTOR, search_query),
            )
            .filter(search=search_query)
            .order_by("-rank", "name")
        )


class Candidate(models.Model):
    class Kind(models.TextChoices):
        FREELANCER = "freelancer", "Frilansare"
        EMPLOYEE = "employee", "Anställd"
        BOTH = "both", "Båda"

    name = models.CharField(max_length=255, db_collation="sv-SE-x-icu")
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

    objects = CandidateQuerySet.as_manager()

    class Meta:
        ordering = ["name"]
        indexes = [
            GinIndex(CANDIDATE_SEARCH_VECTOR, name="candidate_search_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(",") if skill.strip()]


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
