import uuid

from django.db import models

from core.managers import TenantManager


class Report(models.Model):
    """
    Weekly/periodic report storing both raw computed data and polished content.

    Invariants:
    - INV-001: raw_data is deterministic given identical inputs
    - INV-005: Sections appear in fixed SectionType order
    - INV-009: Empty periods produce valid reports with "No data" messages
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    class ReportType(models.TextChoices):
        WEEKLY_OUTLOOK = "weekly_outlook", "Weekly Outlook"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="reports"
    )
    report_type = models.TextField(choices=ReportType.choices)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.TextField(choices=Status.choices, default=Status.PENDING)
    raw_data = models.JSONField(null=True, blank=True)
    polished_content = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    task_id = models.TextField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        db_table = "reports"
        indexes = [
            models.Index(fields=["tenant", "-created_at"], name="idx_reports_tenant"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "report_type", "period_start", "period_end"],
                name="uq_report_tenant_type_period",
            )
        ]


class ReportSection(models.Model):
    """
    Individual section of a report with raw and polished content.

    INV-005: Sections always appear in SectionType enum order.
    """

    class SectionType(models.TextChoices):
        EXEC_SUMMARY = "exec_summary", "Executive Summary"
        WHATS_CHANGED = "whats_changed", "What's Changed"
        WHATS_WORKING = "whats_working", "What's Working"
        NEEDS_ATTENTION = "needs_attention", "Needs Attention"
        RECOMMENDATIONS = "recommendations", "Top Recommendations"
        DECISIONS_MADE = "decisions_made", "Decisions This Week"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="report_sections"
    )
    report = models.ForeignKey(
        "reports.Report", on_delete=models.CASCADE, related_name="sections"
    )
    section_type = models.TextField(choices=SectionType.choices)
    order = models.IntegerField()
    raw_content = models.JSONField()
    polished_content = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        db_table = "report_sections"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["report", "section_type"],
                name="uq_section_report_type",
            )
        ]
