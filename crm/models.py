from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

# "simple" config: no stemming or stop words; skills, names and places
# should match literally. Must stay identical to the GinIndex expression
# in Candidate.Meta for searches to use the index.
CANDIDATE_SEARCH_VECTOR = SearchVector("name", "location", "skills", config="simple")


class User(AbstractUser):
    pass


class Company(models.Model):
    name = models.CharField(max_length=255, db_collation="sv-SE-x-icu")
    location = models.CharField(max_length=255, blank=True, db_index=True)
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
    location = models.CharField(max_length=255, blank=True, db_index=True)
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

    @property
    def is_flagged(self):
        # The reason keeps the flag alive if the flagger is deleted
        # (flagged_by is SET_NULL).
        return self.flagged_by_id is not None or bool(self.flag_reason)


class Lead(models.Model):
    class Stage(models.TextChoices):
        IN_PROGRESS = "in_progress", "Pågående"
        QUOTE = "quote", "Offert"
        INTERVIEW = "interview", "Intervju"
        WON = "won", "Vunnen"
        LOST = "lost", "Förlorad"

    name = models.CharField(max_length=255, db_collation="sv-SE-x-icu")
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="leads"
    )
    expected_value = models.DecimalField(  # SEK
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    contact = models.ForeignKey(
        Contact,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="leads",
    )
    stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.IN_PROGRESS
    )
    candidates = models.ManyToManyField(Candidate, blank=True, related_name="leads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.contact and self.contact.company_id != self.company_id:
            raise ValidationError({"contact": "Kontakten tillhör inte företaget."})


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


class CandidateComment(BaseComment):
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"Comment on {self.candidate} by {self.user}"
