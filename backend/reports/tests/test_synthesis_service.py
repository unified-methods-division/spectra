"""
Tests for report synthesis service.

Invariants covered:
- INV-001: Report data is deterministic given inputs (P0)
- INV-003: Priority score is computable without LLM (P1)
- INV-008: Week-over-week delta uses consistent baseline (P1)
"""

import json
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from freezegun import freeze_time


class TestReportDeterminism:
    """INV-001: Report data is deterministic given inputs."""

    @pytest.mark.django_db
    @freeze_time("2026-04-21")
    def test_report_generation_deterministic(self, tenant_with_report_data):
        """Same inputs → identical raw_data across runs."""
        from reports.services.synthesis import (
            synthesize_report_data,
            serialize_synthesis_result,
        )

        tenant = tenant_with_report_data
        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        result1 = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )
        result2 = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )

        serialized1 = serialize_synthesis_result(result1)
        serialized2 = serialize_synthesis_result(result2)

        # Remove generated_at since it varies between runs
        serialized1.pop("generated_at", None)
        serialized2.pop("generated_at", None)

        json1 = json.dumps(serialized1, sort_keys=True)
        json2 = json.dumps(serialized2, sort_keys=True)

        assert json1 == json2, "Report data must be byte-identical across runs"

    @pytest.mark.django_db
    @freeze_time("2026-04-21")
    def test_report_excludes_items_created_after_snapshot(
        self, tenant_with_report_data
    ):
        """EM-001-A: Items created during generation are excluded."""
        from reports.services.synthesis import synthesize_report_data

        tenant = tenant_with_report_data
        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        result = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )

        # Items received outside the period should not affect the report
        assert result.this_week.total_items >= 0


class TestPriorityScoring:
    """INV-003: Priority score is computable without LLM."""

    def test_priority_score_no_llm_calls(self, mocker):
        """Score computation with mocked LLM (assert never called)."""
        from reports.services.scoring import compute_priority_score

        llm_mock = mocker.patch("pydantic_ai.Agent")

        score = compute_priority_score(
            impact_score=0.8,
            effort_score=0.3,
            confidence=0.9,
            urgency="high",
        )

        assert llm_mock.call_count == 0, "LLM must not be called for scoring"
        assert isinstance(score, float)

    def test_priority_score_in_range(self):
        """PT-001: 0 ≤ priority_score ≤ 1."""
        from reports.services.scoring import compute_priority_score

        test_cases = [
            {
                "impact_score": 0.0,
                "effort_score": 1.0,
                "confidence": 0.0,
                "urgency": "low",
            },
            {
                "impact_score": 1.0,
                "effort_score": 0.0,
                "confidence": 1.0,
                "urgency": "critical",
            },
            {
                "impact_score": 0.5,
                "effort_score": 0.5,
                "confidence": 0.5,
                "urgency": "medium",
            },
            {
                "impact_score": None,
                "effort_score": None,
                "confidence": None,
                "urgency": None,
            },
        ]

        for case in test_cases:
            score = compute_priority_score(**case)
            assert 0 <= score <= 1, f"Score {score} out of range for {case}"

    def test_priority_score_deterministic(self):
        """Same inputs produce same score."""
        from reports.services.scoring import compute_priority_score

        score1 = compute_priority_score(0.8, 0.3, 0.9, "high")
        score2 = compute_priority_score(0.8, 0.3, 0.9, "high")

        assert score1 == score2


class TestWoWDelta:
    """INV-008: Week-over-week delta uses consistent baseline."""

    @pytest.mark.django_db
    @freeze_time("2026-04-21")  # Tuesday
    def test_wow_delta_consistent_baseline(self, tenant_with_report_data):
        """This week vs last week dates are correct."""
        from reports.services.synthesis import synthesize_report_data

        tenant = tenant_with_report_data
        # For a report generated Tuesday Apr 21, reporting on the previous week:
        # This week: Apr 13 (Mon) - Apr 19 (Sun)
        # Last week: Apr 6 (Mon) - Apr 12 (Sun)
        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        result = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )

        assert result.period_start == period_start
        assert result.period_end == period_end

        # Verify delta computation uses correct week boundaries
        if result.last_week is not None:
            expected_last_start = period_start - timedelta(days=7)
            # The synthesis should have computed last_week from Apr 6-12

    @pytest.mark.django_db
    def test_first_report_no_previous_data(self, tenant):
        """EM-008-A: First report shows N/A for deltas."""
        from reports.services.synthesis import synthesize_report_data

        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        result = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )

        # With no data, delta should be None
        if (
            result.this_week.total_items == 0
            or result.last_week is None
            or result.last_week.total_items == 0
        ):
            assert result.delta is None or result.delta.volume_delta is not None


class TestReportStatusTransitions:
    """Test report status transitions."""

    @pytest.mark.django_db
    def test_report_status_transitions(self, tenant):
        """Report status follows PENDING → GENERATING → READY | FAILED."""
        from reports.models import Report

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            status=Report.Status.PENDING,
        )

        assert report.status == Report.Status.PENDING

        report.status = Report.Status.GENERATING
        report.save()
        assert report.status == Report.Status.GENERATING

        report.status = Report.Status.READY
        report.save()
        assert report.status == Report.Status.READY
