"""
Section assembly service.

INV-005: Report sections assemble in fixed order.
INV-009: Empty period produces valid report.
"""

from reports.models import Report, ReportSection
from reports.services.synthesis import SynthesisResult


SECTION_ORDER = [
    ReportSection.SectionType.EXEC_SUMMARY,
    ReportSection.SectionType.WHATS_CHANGED,
    ReportSection.SectionType.WHATS_WORKING,
    ReportSection.SectionType.NEEDS_ATTENTION,
    ReportSection.SectionType.RECOMMENDATIONS,
    ReportSection.SectionType.DECISIONS_MADE,
]


def assemble_sections(
    report: Report,
    synthesis: SynthesisResult,
) -> list[ReportSection]:
    """
    Assemble report sections in fixed order.

    INV-005: Sections always appear in SectionType enum order.
    INV-009: Empty data produces valid sections with "No data" content.
    """
    sections = []

    for order, section_type in enumerate(SECTION_ORDER):
        raw_content = _build_section_content(section_type, synthesis)

        section = ReportSection(
            tenant=report.tenant,
            report=report,
            section_type=section_type,
            order=order,
            raw_content=raw_content,
        )
        sections.append(section)

    return sections


def _build_section_content(
    section_type: str,
    synthesis: SynthesisResult,
) -> dict:
    """Build raw content for a section type."""
    builders = {
        ReportSection.SectionType.EXEC_SUMMARY: _build_exec_summary,
        ReportSection.SectionType.WHATS_CHANGED: _build_whats_changed,
        ReportSection.SectionType.WHATS_WORKING: _build_whats_working,
        ReportSection.SectionType.NEEDS_ATTENTION: _build_needs_attention,
        ReportSection.SectionType.RECOMMENDATIONS: _build_recommendations,
        ReportSection.SectionType.DECISIONS_MADE: _build_decisions,
    }

    builder = builders.get(section_type)
    if builder:
        return builder(synthesis)
    return {"error": f"Unknown section type: {section_type}"}


def _build_exec_summary(s: SynthesisResult) -> dict:
    """Executive summary: key metrics and top themes."""
    if s.this_week.total_items == 0:
        return {"empty": True, "message": "No feedback received this week."}

    # Get top 3 themes by count
    top_themes = sorted(
        s.this_week.theme_counts.items(), key=lambda x: -x[1]
    )[:3]

    return {
        "total_items": s.this_week.total_items,
        "volume_change": s.delta.volume_delta if s.delta else None,
        "accuracy": s.this_week.accuracy,
        "accuracy_change": s.delta.accuracy_delta if s.delta else None,
        "alerts_count": s.this_week.alerts_count,
        "sentiment_distribution": s.this_week.sentiment_distribution,
        "urgency_distribution": s.this_week.urgency_distribution,
        "top_themes": [{"name": t[0], "count": t[1]} for t in top_themes],
    }


def _build_whats_changed(s: SynthesisResult) -> dict:
    """What's changed: volume, sentiment, new themes."""
    if not s.delta:
        return {"empty": True, "message": "No previous data for comparison."}

    return {
        "volume_delta": s.delta.volume_delta,
        "sentiment_delta": s.delta.sentiment_delta,
        "new_themes": s.delta.new_themes,
        "rising_themes": s.delta.rising_themes,
        "declining_themes": s.delta.declining_themes,
    }


def _build_whats_working(s: SynthesisResult) -> dict:
    """What's working: positive trends, improving themes."""
    positive_pct = s.this_week.sentiment_distribution.get("positive", 0)

    working_themes = s.delta.rising_themes[:3] if s.delta else []

    return {
        "positive_sentiment_pct": positive_pct,
        "improving_themes": working_themes,
        "accuracy": s.this_week.accuracy,
    }


def _build_needs_attention(s: SynthesisResult) -> dict:
    """Needs attention: negative trends, declining themes, high urgency."""
    negative_pct = s.this_week.sentiment_distribution.get("negative", 0)
    high_urgency_pct = s.this_week.urgency_distribution.get("high", 0)

    attention_items = []
    
    # Flag high negative sentiment even without delta
    if negative_pct > 0.5:
        attention_items.append(
            {
                "type": "high_negative_sentiment",
                "message": f"{negative_pct:.0%} negative sentiment",
            }
        )
    
    # Flag high urgency
    if high_urgency_pct > 0.5:
        attention_items.append(
            {
                "type": "high_urgency",
                "message": f"{high_urgency_pct:.0%} high urgency items",
            }
        )
    
    # Top problem themes (by count)
    top_themes = sorted(
        s.this_week.theme_counts.items(), key=lambda x: -x[1]
    )[:3]
    for theme, count in top_themes:
        attention_items.append(
            {
                "type": "top_theme",
                "theme": theme,
                "count": count,
            }
        )
    
    if s.delta:
        if s.delta.volume_delta > 0.5:
            attention_items.append(
                {
                    "type": "volume_spike",
                    "message": f"Volume increased {s.delta.volume_delta:.0%}",
                }
            )
        if s.delta.sentiment_delta.get("negative", 0) > 0.1:
            attention_items.append(
                {
                    "type": "sentiment_decline",
                    "message": "Negative sentiment increased significantly",
                }
            )
        for theme in s.delta.declining_themes[:3]:
            attention_items.append(
                {
                    "type": "theme_decline",
                    "theme": theme,
                }
            )

    return {
        "negative_sentiment_pct": negative_pct,
        "high_urgency_pct": high_urgency_pct,
        "attention_items": attention_items,
        "alerts_count": s.this_week.alerts_count,
    }


def _build_recommendations(s: SynthesisResult) -> dict:
    """Top recommendations with scores."""
    if not s.top_recommendations:
        return {"empty": True, "message": "No recommendations this week."}

    return {
        "recommendations": s.top_recommendations,
        "count": len(s.top_recommendations),
    }


def _build_decisions(s: SynthesisResult) -> dict:
    """Decisions made this week."""
    total = sum(s.decisions_summary.values())
    if total == 0:
        return {"empty": True, "message": "No decisions made this week."}

    return {
        "accepted": s.decisions_summary["accepted"],
        "dismissed": s.decisions_summary["dismissed"],
        "pending": s.decisions_summary["needs_more_evidence"],
        "total": total,
    }
