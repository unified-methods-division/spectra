from __future__ import annotations

from dataclasses import dataclass, field

from analysis.models import Correction, GoldSetItem


@dataclass
class EvalResult:
    field_accuracy: dict[str, float] = field(default_factory=dict)
    theme_precision: float = 0.0
    theme_recall: float = 0.0
    overall_accuracy: float = 0.0
    items_evaluated: int = 0


def run_gold_eval(tenant_id: str) -> EvalResult:
    gold_items = GoldSetItem.objects.filter(
        tenant_id=tenant_id
    ).select_related("feedback_item").prefetch_related("feedback_item__corrections")

    if not gold_items.exists():
        return EvalResult()

    sentiment_matches = 0
    urgency_matches = 0
    total = 0
    theme_intersection_sum = 0
    theme_ai_sum = 0
    theme_gold_sum = 0

    for gold in gold_items:
        total += 1
        item = gold.feedback_item
        corrections = item.corrections.all()

        earliest_by_field: dict[str, Correction] = {}
        for c in corrections:
            earliest_by_field.setdefault(c.field_corrected, c)

        ai_sentiment = (
            earliest_by_field["sentiment"].ai_value
            if "sentiment" in earliest_by_field
            else item.sentiment
        )
        if str(ai_sentiment) == str(gold.gold_sentiment):
            sentiment_matches += 1

        ai_urgency = (
            earliest_by_field["urgency"].ai_value
            if "urgency" in earliest_by_field
            else item.urgency
        )
        if str(ai_urgency) == str(gold.gold_urgency):
            urgency_matches += 1

        ai_themes = set(
            earliest_by_field["themes"].ai_value
            if "themes" in earliest_by_field
            else (item.themes or [])
        )
        gold_themes = set(gold.gold_themes or [])
        intersection = ai_themes & gold_themes
        theme_intersection_sum += len(intersection)
        theme_ai_sum += len(ai_themes)
        theme_gold_sum += len(gold_themes)

    sentiment_acc = sentiment_matches / total if total > 0 else 0.0
    urgency_acc = urgency_matches / total if total > 0 else 0.0
    theme_precision = theme_intersection_sum / theme_ai_sum if theme_ai_sum > 0 else 0.0
    theme_recall = theme_intersection_sum / theme_gold_sum if theme_gold_sum > 0 else 0.0
    overall = (sentiment_matches + urgency_matches) / (total * 2) if total > 0 else 0.0

    return EvalResult(
        field_accuracy={"sentiment": sentiment_acc, "urgency": urgency_acc},
        theme_precision=round(theme_precision, 4),
        theme_recall=round(theme_recall, 4),
        overall_accuracy=round(overall, 4),
        items_evaluated=total,
    )