import uuid

from django.db import models


class Correction(models.Model):
    class CorrectedField(models.TextChoices):
        SENTIMENT = "sentiment", "Sentiment"
        THEMES = "themes", "Themes"
        URGENCY = "urgency", "Urgency"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback_item = models.ForeignKey(
        "ingestion.FeedbackItem",
        on_delete=models.CASCADE,
        related_name="corrections",
    )
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="corrections"
    )
    field_corrected = models.TextField(choices=CorrectedField.choices)
    ai_value = models.JSONField()
    human_value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "corrections"
        indexes = [
            models.Index(fields=["tenant", "created_at"], name="idx_corrections_tenant")
        ]


class CorrectionDisagreement(models.Model):
    class ResolutionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="correction_disagreements"
    )
    feedback_item = models.ForeignKey(
        "ingestion.FeedbackItem",
        on_delete=models.CASCADE,
        related_name="correction_disagreements",
    )
    field_corrected = models.TextField(choices=Correction.CorrectedField.choices)
    correction_ids = models.JSONField()
    resolution_status = models.TextField(
        choices=ResolutionStatus.choices, default=ResolutionStatus.PENDING
    )
    resolved_value = models.JSONField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "correction_disagreements"
        indexes = [
            models.Index(fields=["tenant", "resolution_status"], name="idx_disagree_tenant_status"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "feedback_item", "field_corrected"],
                name="uq_disagree_tenant_item_field",
            ),
        ]


class PromptVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="prompt_versions",
    )
    version = models.IntegerField()
    prompt_template = models.TextField()
    few_shot_examples = models.JSONField(null=True, blank=True)
    accuracy_at_creation = models.FloatField(null=True, blank=True)
    accuracy_current = models.FloatField(null=True, blank=True)
    active = models.BooleanField(default=False)
    regression_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prompt_versions"


class Recommendation(models.Model):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Accepted"
        DISMISSED = "dismissed", "Dismissed"
        NEEDS_MORE_EVIDENCE = "needs_more_evidence", "Needs More Evidence"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    title = models.TextField()
    problem_statement = models.TextField()
    proposed_action = models.TextField()
    impact_score = models.FloatField()
    effort_score = models.FloatField()
    confidence = models.FloatField()
    priority_score = models.FloatField()
    decision_owner = models.TextField(null=True, blank=True)
    status = models.TextField(choices=Status.choices, default=Status.PROPOSED)
    rationale = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recommendations"
        indexes = [
            models.Index(
                fields=["tenant", "status", "-created_at"],
                name="idx_reco_tenant_status",
            )
        ]


class RecommendationEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="recommendation_evidence",
    )
    recommendation = models.ForeignKey(
        "analysis.Recommendation",
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    feedback_item = models.ForeignKey(
        "ingestion.FeedbackItem",
        on_delete=models.CASCADE,
        related_name="recommendation_evidence",
    )
    evidence_weight = models.FloatField(default=1.0)
    selection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_evidence"
        indexes = [
            models.Index(
                fields=["recommendation"],
                name="idx_reco_ev_reco",
            )
        ]


class GoldSetItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="gold_set_items"
    )
    feedback_item = models.ForeignKey(
        "ingestion.FeedbackItem",
        on_delete=models.CASCADE,
        related_name="gold_set_items",
    )
    gold_sentiment = models.TextField()
    gold_urgency = models.TextField()
    gold_themes = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gold_set_items"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "feedback_item"],
                name="uq_goldset_tenant_item",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant"], name="idx_goldset_tenant"),
        ]


class RecommendationOutcome(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="recommendation_outcomes",
    )
    recommendation = models.ForeignKey(
        "analysis.Recommendation",
        on_delete=models.CASCADE,
        related_name="outcomes",
    )
    measured_at = models.DateField()
    metric_name = models.TextField()
    baseline_value = models.FloatField()
    current_value = models.FloatField()
    delta = models.FloatField()
    interpretation = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_outcomes"
        constraints = [
            models.UniqueConstraint(
                fields=["recommendation", "metric_name", "measured_at"],
                name="uq_reco_outcome_rec_metric_date",
            ),
        ]
        indexes = [
            models.Index(
                fields=["recommendation", "-measured_at"],
                name="idx_reco_out_reco",
            )
        ]
