"""
Alert creation from report synthesis.

Keeps report synthesis deterministic (pure), but allows the async report generation
task to persist alerts for drill-down navigation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from trends.models import Alert

from .synthesis import SynthesisResult


def create_alerts_for_report(
    *,
    tenant_id: str,
    synthesis: SynthesisResult,
) -> int:
    """
    Create a minimal set of alerts based on synthesis deltas.

    Returns number of newly created alerts.
    """
    created = 0

    delta = synthesis.delta
    if not delta:
        return 0

    period_start = synthesis.period_start.isoformat()
    period_end = synthesis.period_end.isoformat()

    def ensure_alert(
        *,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        explorer_filters: Optional[dict] = None,
        metadata_extra: Optional[dict] = None,
    ):
        nonlocal created

        metadata = {
            "period_start": period_start,
            "period_end": period_end,
            "explorer_filters": explorer_filters or {},
            "delta": asdict(delta),
        }
        if metadata_extra:
            metadata.update(metadata_extra)

        # De-dupe per period+type (best-effort)
        exists = Alert.objects.filter(
            tenant_id=tenant_id,
            alert_type=alert_type,
            metadata__period_start=period_start,
            metadata__period_end=period_end,
        ).exists()
        if exists:
            return

        Alert.objects.create(
            tenant_id=tenant_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            metadata=metadata,
        )
        created += 1

    if delta.volume_delta > 0.5:
        ensure_alert(
            alert_type=Alert.AlertType.VOLUME_SPIKE,
            severity=Alert.Severity.WARNING,
            title="Volume spike",
            description=f"Feedback volume increased by {delta.volume_delta:.0%} week-over-week.",
            explorer_filters={},
        )

    if delta.sentiment_delta.get("negative", 0) > 0.1:
        ensure_alert(
            alert_type=Alert.AlertType.SENTIMENT_SHIFT,
            severity=Alert.Severity.WARNING,
            title="Negative sentiment rising",
            description="Negative sentiment increased significantly week-over-week.",
            explorer_filters={"sentiment": "negative"},
        )

    for theme in (delta.new_themes or [])[:3]:
        ensure_alert(
            alert_type=Alert.AlertType.NEW_THEME,
            severity=Alert.Severity.INFO,
            title="New theme detected",
            description=f"New theme appeared: {theme}",
            explorer_filters={"theme": theme},
            metadata_extra={"theme": theme},
        )

    return created

