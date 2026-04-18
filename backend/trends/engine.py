import logging
from collections import defaultdict
from datetime import date

from analysis.models import Correction
from ingestion.models import FeedbackItem
from trends.models import TrendSnapshot

logger = logging.getLogger(__name__)


def compute_daily_accuracy(tenant_id: str, snapshot_date: date) -> TrendSnapshot:
    """Compute the daily accuracy for a tenant on a given date."""

    items = FeedbackItem.objects.filter(
        tenant_id=tenant_id, created_at__date=snapshot_date
    )
    item_count = items.count()

    if item_count == 0:
        logger.info(
            "No feedback items for tenant=%s on date=%s, snapshot will be empty",
            tenant_id,
            snapshot_date,
        )

    corrections = Correction.objects.filter(feedback_item__in=items).order_by(
        "created_at"
    )

    earliest_by_item_field: dict[tuple, Correction] = {}
    for c in corrections:
        key = (c.feedback_item_id, c.field_corrected)
        earliest_by_item_field.setdefault(key, c)

    theme_stats = defaultdict(lambda: {"total": 0, "corrected": 0})
    sentiment_stats = defaultdict(lambda: {"total": 0, "corrected": 0})
    urgency_stats = defaultdict(lambda: {"total": 0, "corrected": 0})

    for item in items:
        sentiment_corr = earliest_by_item_field.get((item.id, "sentiment"))
        urgency_corr = earliest_by_item_field.get((item.id, "urgency"))
        themes_corr = earliest_by_item_field.get((item.id, "themes"))

        ai_sentiment = sentiment_corr.ai_value if sentiment_corr else item.sentiment
        if ai_sentiment:
            sentiment_stats[ai_sentiment]["total"] += 1
            if sentiment_corr:
                sentiment_stats[ai_sentiment]["corrected"] += 1

        ai_urgency = urgency_corr.ai_value if urgency_corr else item.urgency
        if ai_urgency:
            urgency_stats[ai_urgency]["total"] += 1
            if urgency_corr:
                urgency_stats[ai_urgency]["corrected"] += 1

        ai_themes = set(themes_corr.ai_value if themes_corr else (item.themes or []))
        for theme in ai_themes:
            theme_stats[theme]["total"] += 1
            if themes_corr:
                theme_stats[theme]["corrected"] += 1

    def calc_accuracy(stats: dict) -> dict[str, float]:
        return {
            label: round(
                (s["total"] - s["corrected"]) / s["total"] if s["total"] > 0 else 0,
                2,
            )
            for label, s in stats.items()
        }

    total_predictions = (
        sum(s["total"] for s in theme_stats.values())
        + sum(s["total"] for s in sentiment_stats.values())
        + sum(s["total"] for s in urgency_stats.values())
    )
    total_corrections = (
        sum(s["corrected"] for s in theme_stats.values())
        + sum(s["corrected"] for s in sentiment_stats.values())
        + sum(s["corrected"] for s in urgency_stats.values())
    )

    overall_accuracy = round(
        (total_predictions - total_corrections) / total_predictions
        if total_predictions > 0
        else 0,
        2,
    )

    snapshot, _ = TrendSnapshot.objects.update_or_create(
        tenant_id=tenant_id,
        snapshot_date=snapshot_date,
        defaults={
            "metrics": {
                "total_accuracy": overall_accuracy,
                "accuracy_by_theme": calc_accuracy(theme_stats),
                "accuracy_by_sentiment": calc_accuracy(sentiment_stats),
                "accuracy_by_urgency": calc_accuracy(urgency_stats),
            }
        },
    )

    logger.info(
        "Snapshot for tenant=%s date=%s: %d items, %d predictions, %d corrections, %.0f%% accuracy",
        tenant_id,
        snapshot_date,
        item_count,
        total_predictions,
        total_corrections,
        overall_accuracy * 100,
    )

    return snapshot
