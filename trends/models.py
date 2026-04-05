import uuid

from django.db import models


class TrendSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="trend_snapshots")
    snapshot_date = models.DateField()
    metrics = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trend_snapshots"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "snapshot_date"],
                name="uniq_trend_snapshot_tenant_date",
            )
        ]


class Alert(models.Model):
    class AlertType(models.TextChoices):
        VOLUME_SPIKE = "volume_spike", "Volume Spike"
        SENTIMENT_SHIFT = "sentiment_shift", "Sentiment Shift"
        NEW_THEME = "new_theme", "New Theme"
        URGENCY_SURGE = "urgency_surge", "Urgency Surge"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("core.Tenant", on_delete=models.CASCADE, related_name="alerts")
    alert_type = models.TextField(choices=AlertType.choices)
    severity = models.TextField(choices=Severity.choices)
    title = models.TextField()
    description = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    acknowledged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "alerts"
        indexes = [
            models.Index(fields=["tenant", "-created_at"], name="idx_alerts_tenant"),
        ]
