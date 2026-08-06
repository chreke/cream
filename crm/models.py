import operator
import re
from functools import reduce

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.dispatch import receiver

# "simple" config: no stemming or stop words; skills and names should match
# literally. Must stay identical to the GinIndex expression in Candidate.Meta
# for searches to use the index.
CANDIDATE_SEARCH_VECTOR = SearchVector("name", "skills", config="simple")


class User(AbstractUser):
    pass


class Tag(models.Model):
    name = models.CharField(max_length=100, db_collation="sv-SE-x-icu")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_tag_name_ci"),
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Taggens namn får inte vara tomt."})
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    tags = models.ManyToManyField(Tag, blank=True, related_name="companies")

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
        """Word-prefix search over name/skills, most relevant first.

        All query terms must match. Exact-word matches rank ahead of
        prefix-only matches, followed by full-text relevance and name.
        """
        # Using only letter/digit runs keeps the raw tsquery syntax below safe
        # and mirrors how PostgreSQL tokenizes punctuation-separated input.
        terms = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if not terms:
            return self.none()

        prefix_queries = [
            SearchQuery(f"{term}:*", config="simple", search_type="raw")
            for term in terms
        ]
        prefix_query = reduce(operator.and_, prefix_queries)
        exact_query = SearchQuery(" ".join(terms), config="simple")
        return (
            self.annotate(
                search=CANDIDATE_SEARCH_VECTOR,
                exact_rank=SearchRank(CANDIDATE_SEARCH_VECTOR, exact_query),
                rank=SearchRank(CANDIDATE_SEARCH_VECTOR, prefix_query),
            )
            .filter(search=prefix_query)
            .order_by("-exact_rank", "-rank", "name")
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


class Resume(models.Model):
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="resumes"
    )
    file = models.FileField(upload_to="resumes/%Y/%m/", max_length=255)
    # Django mangles the stored name (sanitization, dedup suffixes), so the
    # original is kept for display and as the download filename.
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.filename} ({self.candidate})"


@receiver(models.signals.post_delete, sender=Resume)
def _delete_resume_file(sender, instance, **kwargs):
    """Files are never deleted from storage by Django itself. A signal
    (rather than a delete() override) also covers rows cascade-deleted
    with their candidate."""
    instance.file.delete(save=False)


class LeadQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)


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
    # Soft delete (specs/013): hidden from the pipeline but kept so that
    # candidate pages can still show which companies a candidate was sent to.
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = LeadQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    @property
    def is_deleted(self):
        return self.deleted_at is not None

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


class LeadComment(BaseComment):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return f"Comment on {self.lead} by {self.user}"


class CandidateComment(BaseComment):
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"Comment on {self.candidate} by {self.user}"
