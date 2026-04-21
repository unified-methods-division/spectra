"""
Deterministic priority scoring service.

INV-003: Priority score is computable without LLM.
"""

from dataclasses import dataclass
from typing import Optional

from analysis.models import Recommendation


@dataclass
class ScoringWeights:
    """Tunable weights for priority scoring."""

    impact: float = 0.4
    effort_inverse: float = 0.2
    confidence: float = 0.2
    urgency: float = 0.2

    def __post_init__(self):
        total = self.impact + self.effort_inverse + self.confidence + self.urgency
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


URGENCY_MULTIPLIERS = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}


def compute_priority_score(
    impact_score: Optional[float],
    effort_score: Optional[float],
    confidence: Optional[float],
    urgency: Optional[str],
    weights: Optional[ScoringWeights] = None,
) -> float:
    """
    Compute priority score for a recommendation.

    Formula:
        score = (impact * w_i) + ((1 - effort) * w_e) + (confidence * w_c) + (urgency_mult * w_u)

    All inputs clamped to [0, 1]. Missing values default to 0.5.
    Output bounded [0, 1].

    INV-003: This function MUST NOT call any LLM.
    """
    weights = weights or ScoringWeights()

    impact = _clamp(impact_score, default=0.5)
    effort = _clamp(effort_score, default=0.5)
    conf = _clamp(confidence, default=0.5)
    urgency_mult = URGENCY_MULTIPLIERS.get(urgency, 0.5)

    effort_contrib = 1.0 - effort

    raw_score = (
        (impact * weights.impact)
        + (effort_contrib * weights.effort_inverse)
        + (conf * weights.confidence)
        + (urgency_mult * weights.urgency)
    )

    return round(_clamp(raw_score), 4)


def _clamp(value: Optional[float], default: float = 0.5) -> float:
    """Clamp value to [0, 1], using default if None."""
    if value is None:
        return default
    return max(0.0, min(1.0, value))


def rank_recommendations(
    recommendations: list[Recommendation],
    weights: Optional[ScoringWeights] = None,
) -> list[tuple[Recommendation, float]]:
    """
    Rank recommendations by priority score.

    Returns list of (recommendation, score) tuples sorted by score descending.
    Tie-breaker: created_at ascending (older first).
    """
    scored = []
    for rec in recommendations:
        score = compute_priority_score(
            impact_score=rec.impact_score,
            effort_score=rec.effort_score,
            confidence=rec.confidence,
            urgency=_get_max_urgency(rec),
            weights=weights,
        )
        scored.append((rec, score))

    scored.sort(key=lambda x: (-x[1], x[0].created_at))
    return scored


def _get_max_urgency(recommendation: Recommendation) -> Optional[str]:
    """Get highest urgency from recommendation's evidence items."""
    try:
        evidence_items = recommendation.evidence.select_related("feedback_item").all()
        urgencies = [
            e.feedback_item.urgency for e in evidence_items if e.feedback_item.urgency
        ]
        if not urgencies:
            return None

        priority_order = ["critical", "high", "medium", "low"]
        for urgency in priority_order:
            if urgency in urgencies:
                return urgency
    except Exception:
        pass
    return None
