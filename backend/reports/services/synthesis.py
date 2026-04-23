"""
Report synthesis engine.

INV-001: Report data is deterministic given inputs.
INV-008: Week-over-week delta uses consistent baseline.
"""

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Optional

from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from analysis.models import Recommendation, RecommendationEvidence
from ingestion.models import FeedbackItem
from trends.models import TrendSnapshot, Alert
from reports.services.scoring import rank_recommendations


@dataclass
class PeriodMetrics:
    """Metrics for a single period."""

    total_items: int
    sentiment_distribution: dict[str, float]
    urgency_distribution: dict[str, float]
    theme_counts: dict[str, int]
    accuracy: float
    alerts_count: int


@dataclass
class DeltaMetrics:
    """Week-over-week delta metrics."""

    volume_delta: float
    sentiment_delta: dict[str, float]
    accuracy_delta: float
    new_themes: list[str]
    rising_themes: list[str]
    declining_themes: list[str]


@dataclass
class SynthesisResult:
    """Complete synthesis output for a report."""

    period_start: date
    period_end: date
    this_week: PeriodMetrics
    last_week: Optional[PeriodMetrics]
    delta: Optional[DeltaMetrics]
    top_recommendations: list[dict]
    decisions_summary: dict
    generated_at: str


def synthesize_report_data(
    tenant_id: str,
    period_start: date,
    period_end: date,
) -> SynthesisResult:
    """
    Compute all report data deterministically.

    INV-001: Same inputs → identical output.
    INV-008: Week boundaries are Monday-Sunday.

    This function MUST NOT call any LLM.
    """
    this_week = _compute_period_metrics(tenant_id, period_start, period_end)

    last_week_start = period_start - timedelta(days=7)
    last_week_end = period_end - timedelta(days=7)
    last_week = _compute_period_metrics(tenant_id, last_week_start, last_week_end)

    delta = (
        _compute_deltas(this_week, last_week) if last_week.total_items > 0 else None
    )

    # Recommendations belong to a report period via supporting evidence (feedback
    # received in-window), not via Recommendation.created_at (a rec authored later
    # can still cover an earlier week). Legacy rows with no evidence still match
    # on created_at for backward compatibility.
    evidence_in_period = RecommendationEvidence.objects.filter(
        recommendation_id=OuterRef("pk"),
        feedback_item__received_at__date__gte=period_start,
        feedback_item__received_at__date__lte=period_end,
    )
    recommendations = (
        Recommendation.objects.filter(
            tenant_id=tenant_id,
            status__in=["proposed", "accepted"],
        )
        .filter(
            Q(Exists(evidence_in_period))
            | Q(
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
            )
        )
        .distinct()
    )
    ranked = rank_recommendations(list(recommendations))
    top_recs = [
        {
            "id": str(rec.id),
            "title": rec.title,
            "problem_statement": rec.problem_statement,
            "proposed_action": rec.proposed_action,
            "priority_score": round(score, 4),
            "status": rec.status,
        }
        for rec, score in ranked[:5]
    ]

    decisions = _compute_decisions_summary(tenant_id, period_start, period_end)

    return SynthesisResult(
        period_start=period_start,
        period_end=period_end,
        this_week=this_week,
        last_week=last_week if last_week.total_items > 0 else None,
        delta=delta,
        top_recommendations=top_recs,
        decisions_summary=decisions,
        generated_at=timezone.now().isoformat(),
    )


def _compute_period_metrics(
    tenant_id: str,
    start: date,
    end: date,
) -> PeriodMetrics:
    """Compute metrics for a date range."""
    items = FeedbackItem.objects.filter(
        tenant_id=tenant_id,
        received_at__date__gte=start,
        received_at__date__lte=end,
    )

    total = items.count()

    sentiment_counts = items.values("sentiment").annotate(count=Count("id"))
    sentiment_dist = {
        s["sentiment"]: round(s["count"] / total, 4) if total > 0 else 0
        for s in sentiment_counts
        if s["sentiment"]
    }

    urgency_counts = items.values("urgency").annotate(count=Count("id"))
    urgency_dist = {
        u["urgency"]: round(u["count"] / total, 4) if total > 0 else 0
        for u in urgency_counts
        if u["urgency"]
    }

    theme_counts: dict[str, int] = {}
    for item in items.filter(themes__isnull=False):
        for theme in item.themes or []:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    snapshots = TrendSnapshot.objects.filter(
        tenant_id=tenant_id,
        snapshot_date__gte=start,
        snapshot_date__lte=end,
    )
    if snapshots.exists():
        accuracy = round(
            sum(s.metrics.get("total_accuracy", 0) for s in snapshots)
            / snapshots.count(),
            4,
        )
    else:
        accuracy = 0.0

    alerts = Alert.objects.filter(
        tenant_id=tenant_id,
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).count()

    return PeriodMetrics(
        total_items=total,
        sentiment_distribution=sentiment_dist,
        urgency_distribution=urgency_dist,
        theme_counts=theme_counts,
        accuracy=accuracy,
        alerts_count=alerts,
    )


def _compute_deltas(
    this_week: PeriodMetrics,
    last_week: PeriodMetrics,
) -> DeltaMetrics:
    """Compute week-over-week deltas."""
    if last_week.total_items > 0:
        volume_delta = round(
            (this_week.total_items - last_week.total_items) / last_week.total_items,
            4,
        )
    else:
        volume_delta = 1.0 if this_week.total_items > 0 else 0.0

    sentiment_delta = {}
    for sentiment in this_week.sentiment_distribution:
        this_val = this_week.sentiment_distribution.get(sentiment, 0)
        last_val = last_week.sentiment_distribution.get(sentiment, 0)
        sentiment_delta[sentiment] = round(this_val - last_val, 4)

    accuracy_delta = round(this_week.accuracy - last_week.accuracy, 4)

    this_themes = set(this_week.theme_counts.keys())
    last_themes = set(last_week.theme_counts.keys())
    new_themes = list(this_themes - last_themes)

    rising = []
    declining = []
    for theme in this_themes & last_themes:
        this_count = this_week.theme_counts[theme]
        last_count = last_week.theme_counts.get(theme, 0)
        if last_count > 0:
            change = (this_count - last_count) / last_count
            if change > 0.2:
                rising.append(theme)
            elif change < -0.2:
                declining.append(theme)

    return DeltaMetrics(
        volume_delta=volume_delta,
        sentiment_delta=sentiment_delta,
        accuracy_delta=accuracy_delta,
        new_themes=sorted(new_themes),
        rising_themes=sorted(rising),
        declining_themes=sorted(declining),
    )


def _compute_decisions_summary(
    tenant_id: str,
    start: date,
    end: date,
) -> dict:
    """Summarize recommendation decisions for the period."""
    recommendations = Recommendation.objects.filter(
        tenant_id=tenant_id,
        decided_at__date__gte=start,
        decided_at__date__lte=end,
    )

    return {
        "accepted": recommendations.filter(status="accepted").count(),
        "dismissed": recommendations.filter(status="dismissed").count(),
        "needs_more_evidence": recommendations.filter(
            status="needs_more_evidence"
        ).count(),
    }


def serialize_synthesis_result(result: SynthesisResult) -> dict:
    """
    Convert SynthesisResult to JSON-serializable dict.

    INV-001: Output must be deterministic. Sort all lists, use consistent key order.
    """
    data = asdict(result)

    data["period_start"] = result.period_start.isoformat()
    data["period_end"] = result.period_end.isoformat()

    if data["this_week"]["theme_counts"]:
        data["this_week"]["theme_counts"] = dict(
            sorted(data["this_week"]["theme_counts"].items())
        )
    if data.get("last_week") and data["last_week"]["theme_counts"]:
        data["last_week"]["theme_counts"] = dict(
            sorted(data["last_week"]["theme_counts"].items())
        )

    return data
