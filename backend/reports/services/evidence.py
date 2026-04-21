"""
Evidence selection service.

INV-004: Evidence selection is traceable.
"""

from dataclasses import dataclass
from typing import Optional

from django.db.models import QuerySet

from analysis.models import Recommendation, RecommendationEvidence
from ingestion.models import FeedbackItem


@dataclass
class SelectionCriteria:
    """Criteria for evidence selection."""

    max_items: int = 5
    prefer_recent: bool = True
    prefer_urgent: bool = True
    require_theme_match: bool = True


URGENCY_PRIORITY = {"critical": 4, "high": 3, "medium": 2, "low": 1, None: 0}


def select_evidence(
    recommendation: Recommendation,
    candidate_items: QuerySet[FeedbackItem],
    criteria: Optional[SelectionCriteria] = None,
) -> list[RecommendationEvidence]:
    """
    Select top N feedback items as evidence for a recommendation.

    INV-004: Every returned evidence MUST have a non-null selection_reason.

    Selection algorithm:
    1. Filter to items matching recommendation themes (if require_theme_match)
    2. Sort by urgency (desc) then recency (desc)
    3. Take top N
    4. Create evidence links with selection reason

    Returns list of RecommendationEvidence objects (not yet saved).
    """
    criteria = criteria or SelectionCriteria()

    rec_themes = _extract_themes(recommendation)

    if criteria.require_theme_match and rec_themes:
        filtered = [
            item
            for item in candidate_items
            if _has_theme_overlap(item.themes, rec_themes)
        ]
    else:
        filtered = list(candidate_items)

    if not filtered:
        return []

    def sort_key(item: FeedbackItem):
        urgency_score = URGENCY_PRIORITY.get(item.urgency, 0)
        recency_score = item.received_at.timestamp() if item.received_at else 0
        return (
            -urgency_score if criteria.prefer_urgent else 0,
            -recency_score if criteria.prefer_recent else 0,
        )

    filtered.sort(key=sort_key)
    selected = filtered[: criteria.max_items]

    reason_parts = []
    if criteria.prefer_urgent:
        reason_parts.append("urgency")
    if criteria.prefer_recent:
        reason_parts.append("recency")

    reason = f"top {len(selected)} by {' + '.join(reason_parts)}"
    if rec_themes:
        reason += f" | theme match: {', '.join(rec_themes[:3])}"

    evidence_list = []
    for i, item in enumerate(selected):
        evidence = RecommendationEvidence(
            tenant=recommendation.tenant,
            recommendation=recommendation,
            feedback_item=item,
            evidence_weight=1.0 - (i * 0.1),
            selection_reason=reason,
        )
        evidence_list.append(evidence)

    return evidence_list


def _extract_themes(recommendation: Recommendation) -> list[str]:
    """Extract theme keywords from recommendation."""
    themes = []
    if recommendation.rationale and isinstance(recommendation.rationale, dict):
        themes.extend(recommendation.rationale.get("themes", []))
    return themes


def _has_theme_overlap(item_themes: Optional[list], rec_themes: list[str]) -> bool:
    """Check if item has any overlapping themes with recommendation."""
    if not item_themes:
        return False
    return bool(set(item_themes) & set(rec_themes))


def link_evidence_for_recommendations(
    recommendations: list[Recommendation],
    feedback_items: QuerySet[FeedbackItem],
    criteria: Optional[SelectionCriteria] = None,
) -> int:
    """
    Select and persist evidence for multiple recommendations.

    Returns count of evidence links created.
    """
    created_count = 0

    for rec in recommendations:
        if rec.evidence.exists():
            continue

        evidence_list = select_evidence(rec, feedback_items, criteria)

        RecommendationEvidence.objects.bulk_create(
            evidence_list,
            ignore_conflicts=True,
        )
        created_count += len(evidence_list)

    return created_count
