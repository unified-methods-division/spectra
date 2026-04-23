from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from analysis.models import Recommendation, RecommendationOutcome
from ingestion.models import FeedbackItem
from trends.models import TrendSnapshot


@dataclass
class DriftEntry:
    week_start: date
    week_end: date
    accuracy: float
    prev_accuracy: float | None
    delta: float | None


def measure_recommendation_outcome(recommendation_id: str) -> list[RecommendationOutcome]:
    try:
        rec = (
            Recommendation.objects
            .select_related("tenant")
            .prefetch_related("evidence__feedback_item")
            .get(id=recommendation_id)
        )
    except Recommendation.DoesNotExist:
        return []

    if rec.status != Recommendation.Status.ACCEPTED:
        return []

    evidence_items = [ev.feedback_item for ev in rec.evidence.all()]
    if not evidence_items:
        return []

    baseline_total = len(evidence_items)
    baseline_negative = sum(1 for fi in evidence_items if fi.sentiment == FeedbackItem.Sentiment.NEGATIVE)
    baseline_high_urgency = sum(
        1 for fi in evidence_items
        if fi.urgency in (FeedbackItem.Urgency.HIGH, FeedbackItem.Urgency.CRITICAL)
    )

    baseline_negative_pct = baseline_negative / baseline_total if baseline_total else 0.0
    baseline_high_urgency_pct = baseline_high_urgency / baseline_total if baseline_total else 0.0

    cutoff = timezone.now() - timedelta(days=14)
    current_items = list(
        FeedbackItem.objects.filter(
            tenant=rec.tenant,
            processed_at__gte=cutoff,
        )
    )
    current_total = len(current_items) or 1
    current_negative = sum(1 for fi in current_items if fi.sentiment == FeedbackItem.Sentiment.NEGATIVE)
    current_high_urgency = sum(
        1 for fi in current_items
        if fi.urgency in (FeedbackItem.Urgency.HIGH, FeedbackItem.Urgency.CRITICAL)
    )

    current_negative_pct = current_negative / current_total if current_total else 0.0
    current_high_urgency_pct = current_high_urgency / current_total if current_total else 0.0

    metrics = [
        ("negative_sentiment_pct", baseline_negative_pct, current_negative_pct),
        ("high_urgency_pct", baseline_high_urgency_pct, current_high_urgency_pct),
    ]

    today = date.today()
    outcomes = []
    for metric_name, baseline, current in metrics:
        outcomes.append(
            RecommendationOutcome(
                tenant=rec.tenant,
                recommendation=rec,
                measured_at=today,
                metric_name=metric_name,
                baseline_value=round(baseline, 4),
                current_value=round(current, 4),
                delta=round(current - baseline, 4),
            )
        )

    with transaction.atomic():
        Recommendation.objects.select_for_update().filter(pk=rec.pk).first()
        RecommendationOutcome.objects.filter(recommendation_id=recommendation_id).delete()
        RecommendationOutcome.objects.bulk_create(outcomes, ignore_conflicts=True)

    return list(RecommendationOutcome.objects.filter(recommendation_id=recommendation_id))


def compute_drift_delta(tenant_id: str, weeks: int = 4) -> list[DriftEntry]:
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)

    snapshots = list(
        TrendSnapshot.objects.filter(
            tenant_id=tenant_id,
            snapshot_date__gte=start_date,
            snapshot_date__lte=end_date,
        ).order_by("snapshot_date")
    )

    if not snapshots:
        return []

    week_buckets: dict[tuple[int, int], list[float]] = {}
    for snap in snapshots:
        iso = snap.snapshot_date.isocalendar()
        key = (iso[0], iso[1])
        acc = snap.metrics.get("total_accuracy")
        if acc is not None:
            week_buckets.setdefault(key, []).append(acc)

    sorted_weeks = sorted(week_buckets.keys())
    entries: list[DriftEntry] = []

    for i, week_key in enumerate(sorted_weeks):
        accs = week_buckets[week_key]
        avg_acc = sum(accs) / len(accs)

        iso_year, iso_week = week_key
        week_start = date.fromisocalendar(iso_year, iso_week, 1)
        week_end = week_start + timedelta(days=6)

        prev_accuracy = None
        delta = None
        if i > 0:
            prev_key = sorted_weeks[i - 1]
            prev_vals = week_buckets[prev_key]
            prev_accuracy = round(sum(prev_vals) / len(prev_vals), 4)
            delta = round(avg_acc - prev_accuracy, 4)

        entries.append(DriftEntry(
            week_start=week_start,
            week_end=week_end,
            accuracy=round(avg_acc, 4),
            prev_accuracy=prev_accuracy,
            delta=delta,
        ))

    return entries


def compute_weekly_accuracy(tenant_id: str, snapshot_date: date) -> float | None:
    iso = snapshot_date.isocalendar()
    week_start = date.fromisocalendar(iso[0], iso[1], 1)
    week_end = week_start + timedelta(days=6)

    snapshots = TrendSnapshot.objects.filter(
        tenant_id=tenant_id,
        snapshot_date__gte=week_start,
        snapshot_date__lte=week_end,
    )

    accs = [s.metrics.get("total_accuracy") for s in snapshots if s.metrics.get("total_accuracy") is not None]
    if not accs:
        return None
    return round(sum(accs) / len(accs), 4)