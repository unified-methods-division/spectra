"""
Tests for section assembly.

Invariants covered:
- INV-005: Report sections assemble in fixed order (P2)
- INV-009: Empty period produces valid report (P2)
"""

import pytest
from datetime import date
from freezegun import freeze_time


class TestSectionAssembly:
    """INV-005: Section assembly order tests."""

    @pytest.mark.django_db
    def test_sections_in_fixed_order(self, tenant):
        """Sections always appear in SectionType enum order."""
        from reports.models import Report, ReportSection
        from reports.services.sections import assemble_sections, SECTION_ORDER
        from reports.services.synthesis import SynthesisResult, PeriodMetrics

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
        )

        # Create minimal synthesis result
        synthesis = SynthesisResult(
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            this_week=PeriodMetrics(
                total_items=10,
                sentiment_distribution={"positive": 0.5, "negative": 0.3, "neutral": 0.2},
                urgency_distribution={"low": 0.5, "medium": 0.3, "high": 0.2},
                theme_counts={"billing": 5},
                accuracy=0.85,
                alerts_count=1,
            ),
            last_week=None,
            delta=None,
            top_recommendations=[],
            decisions_summary={"accepted": 0, "dismissed": 0, "needs_more_evidence": 0},
            generated_at="2026-04-21T06:00:00Z",
        )

        sections = assemble_sections(report, synthesis)

        # Verify order matches SECTION_ORDER
        for i, section in enumerate(sections):
            assert section.order == i, f"Section {section.section_type} has wrong order"
            assert section.section_type == SECTION_ORDER[i], (
                f"Section at index {i} should be {SECTION_ORDER[i]}, got {section.section_type}"
            )

    @pytest.mark.django_db
    def test_empty_period_valid_report(self, tenant):
        """INV-009: Zero feedback items produces valid report."""
        from reports.models import Report
        from reports.services.sections import assemble_sections
        from reports.services.synthesis import SynthesisResult, PeriodMetrics

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
        )

        # Empty period synthesis
        synthesis = SynthesisResult(
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            this_week=PeriodMetrics(
                total_items=0,
                sentiment_distribution={},
                urgency_distribution={},
                theme_counts={},
                accuracy=0.0,
                alerts_count=0,
            ),
            last_week=None,
            delta=None,
            top_recommendations=[],
            decisions_summary={"accepted": 0, "dismissed": 0, "needs_more_evidence": 0},
            generated_at="2026-04-21T06:00:00Z",
        )

        sections = assemble_sections(report, synthesis)

        # Should still produce all sections
        assert len(sections) == 6

        # Exec summary should have empty message
        exec_section = next(s for s in sections if s.section_type == "exec_summary")
        assert exec_section.raw_content.get("empty") is True
        assert "No feedback" in exec_section.raw_content.get("message", "")
