"""
Tests for dashboard/report sync.

Invariants covered:
- INV-010: Dashboard summary panels reflect same data as report (P0)
"""

import pytest
from datetime import date
from freezegun import freeze_time


class TestDashboardSync:
    """INV-010: Dashboard summary matches report."""

    @pytest.mark.django_db
    @freeze_time("2026-04-21")
    def test_dashboard_summary_matches_report(self, tenant_with_report_data, api_client):
        """Same tenant+period → identical metric values."""
        from reports.models import Report
        from django.utils import timezone

        tenant = tenant_with_report_data

        # Create a ready report with raw_data
        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            status=Report.Status.READY,
            raw_data={
                "this_week": {
                    "total_items": 247,
                    "accuracy": 0.85,
                    "alerts_count": 3,
                },
                "delta": {
                    "volume_delta": 0.15,
                    "accuracy_delta": 0.02,
                },
            },
            generated_at=timezone.now(),
        )

        # Get report summary
        report_response = api_client.get(f"/api/reports/reports/{report.id}/summary/")

        # Get dashboard summary for same period (last-week from perspective of Apr 21)
        dashboard_response = api_client.get(
            "/api/trends/dashboard/summary/",
            {"period": "last-week"},
        )

        assert report_response.status_code == 200
        assert dashboard_response.status_code == 200

        report_data = report_response.json()
        dashboard_data = dashboard_response.json()

        # Assert metrics match
        assert report_data["total_items"] == dashboard_data["total_items"], (
            f"total_items mismatch: report={report_data['total_items']}, dashboard={dashboard_data['total_items']}"
        )
        assert report_data["accuracy"] == dashboard_data["accuracy"], (
            f"accuracy mismatch: report={report_data['accuracy']}, dashboard={dashboard_data['accuracy']}"
        )
        assert report_data["volume_change"] == dashboard_data["volume_change"], (
            f"volume_change mismatch: report={report_data['volume_change']}, dashboard={dashboard_data['volume_change']}"
        )
        assert report_data["accuracy_change"] == dashboard_data["accuracy_change"], (
            f"accuracy_change mismatch: report={report_data['accuracy_change']}, dashboard={dashboard_data['accuracy_change']}"
        )
        assert report_data["alerts_count"] == dashboard_data["alerts_count"], (
            f"alerts_count mismatch: report={report_data['alerts_count']}, dashboard={dashboard_data['alerts_count']}"
        )

    @pytest.mark.django_db
    def test_dashboard_computes_live_without_report(self, tenant, api_client):
        """Dashboard returns summary even without existing report."""
        response = api_client.get(
            "/api/trends/dashboard/summary/",
            {"period": "this-week"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "live"
        assert data["report_id"] is None

    @pytest.mark.django_db
    def test_dashboard_uses_cached_report_data(self, tenant, api_client):
        """Dashboard returns source='report' when report exists."""
        from reports.models import Report
        from django.utils import timezone

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            status=Report.Status.READY,
            raw_data={
                "this_week": {
                    "total_items": 100,
                    "accuracy": 0.9,
                    "alerts_count": 1,
                },
                "delta": None,
            },
            generated_at=timezone.now(),
        )

        response = api_client.get(
            "/api/trends/dashboard/summary/",
            {
                "period": "custom",
                "period_start": "2026-04-13",
                "period_end": "2026-04-19",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "report"
        assert data["report_id"] == str(report.id)
