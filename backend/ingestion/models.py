import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import IvfflatIndex, VectorField
from pydantic import BaseModel, Field
from core.managers import TenantManager


class Source(models.Model):
    class SourceType(models.TextChoices):
        CSV_UPLOAD = "csv_upload", "CSV Upload"
        WEBHOOK = "webhook", "Webhook"
        RSS_PULL = "rss_pull", "RSS Pull"
        API_PULL = "api_pull", "API Pull"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="sources"
    )
    name = models.TextField()
    source_type = models.TextField(choices=SourceType.choices)
    config = models.JSONField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        db_table = "sources"


class FeedbackItem(models.Model):
    class Sentiment(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEGATIVE = "negative", "Negative"
        NEUTRAL = "neutral", "Neutral"
        MIXED = "mixed", "Mixed"

    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="feedback_items",
    )
    source = models.ForeignKey(
        "ingestion.Source",
        on_delete=models.CASCADE,
        related_name="feedback_items",
    )
    external_id = models.TextField(null=True, blank=True)
    content = models.TextField()
    author = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    sentiment = models.TextField(choices=Sentiment.choices, null=True, blank=True)
    sentiment_confidence = models.FloatField(null=True, blank=True)
    urgency = models.TextField(choices=Urgency.choices, null=True, blank=True)
    themes = models.JSONField(null=True, blank=True)
    ai_summary = models.TextField(null=True, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        db_table = "feedback_items"
        indexes = [
            models.Index(fields=["tenant"], name="idx_feedback_tenant"),
            models.Index(fields=["source"], name="idx_feedback_source"),
            models.Index(fields=["tenant", "sentiment"], name="idx_feedback_sentiment"),
            models.Index(
                fields=["tenant", "received_at"], name="idx_feedback_received"
            ),
            models.Index(
                fields=["tenant"],
                name="idx_feedback_unprocessed",
                condition=Q(processed_at__isnull=True),
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="uq_feedback_source_extid",
                condition=Q(external_id__isnull=False),
            ),
        ]

        if "sqlite" not in settings.DATABASES["default"]["ENGINE"]:
            indexes.append(
                IvfflatIndex(
                    name="idx_feedback_embedding",
                    fields=["embedding"],
                    lists=100,
                    opclasses=["vector_cosine_ops"],
                )
            )


class FeedbackAnalysis(BaseModel):
    # sentiment, themes and urgency can be updated in the future via corrections

    # The sentiment determines positive/negative/neutral/mixed. If its not categorially positive, theres probably a reason to extract themes and recommendations from it in the future.
    sentiment: FeedbackItem.Sentiment
    # The urgency determines the priority of the feedback item. This will help us prioritize the recommendations we send tenants
    urgency: FeedbackItem.Urgency
    # Confidence in sentiment can affect urgency and recommendations. if we're confident the sentiment is negative, we can prioritize it more.
    sentiment_confidence: float = Field(
        description="Confidence score for the sentiment analysis",
        ge=0,
        le=1,
    )
    # Themes help us identify the trends in the feedback, we can answer what aspect of their app keeps coming up positively/negatively
    themes: list[str] = Field(
        min_length=2,
        max_length=5,
        description="2-5 theme slugs from the taxonomy, or new slugs if no match found",
    )
    # The summary takes the feedback and generates a 1-2 sentence summary of the feedback item.
    # This will help us quickly understand the feedback item and its context.
    ai_summary: str = Field(
        description="1-2 sentence summary of the feedback item generated by the AI",
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "sentiment": "positive",
                    "sentiment_confidence": 0.9,
                    "urgency": "high",
                    "themes": ["performance", "usability"],
                    "ai_summary": "The user is complaining about the performance of the app and the usability of the app",
                }
            ]
        }
    }


class RoutingConfig(models.Model):
    class LowConfidenceAction(models.TextChoices):
        FLAG = "flag", "Flag"
        SKIP_AI = "skip_ai", "Skip AI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.OneToOneField(
        "ingestion.Source",
        on_delete=models.CASCADE,
        related_name="routing_config",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="routing_configs",
    )
    confidence_threshold = models.FloatField(default=0.85)
    items_below_threshold_action = models.TextField(
        choices=LowConfidenceAction.choices,
        default=LowConfidenceAction.FLAG,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "routing_config"
