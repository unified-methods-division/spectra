"""
Tests for Report API.

Invariants covered:
- INV-007: Report generation never blocks request thread (P1)
"""

import time
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient


class TestReportAPI:
    """INV-007: Report generation never blocks request."""

    @pytest.mark.django_db
    def test_report_api_returns_202_fast(self, tenant, api_client, mocker):
        """POST /api/reports/ < 500ms, status = GENERATING or PENDING.
        
        INV-007: Report generation never blocks request thread.
        In production, task runs async; in tests with CELERY_TASK_ALWAYS_EAGER,
        we mock the task to verify the API response is fast.
        """
        mock_task = mocker.patch("reports.views.generate_report_task.delay")
        mock_task.return_value.id = "test-task-id"
        
        start = time.time()

        response = api_client.post(
            "/api/reports/reports/",
            {
                "report_type": "weekly_outlook",
                "period_start": "2026-04-13",
                "period_end": "2026-04-19",
            },
            format="json",
        )

        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code in [200, 201, 202], f"Expected 2xx, got {response.status_code}"
        assert elapsed_ms < 500, f"API took {elapsed_ms}ms, must be < 500ms"

        data = response.json()
        assert data["status"] in ["pending", "generating", "ready"]
        mock_task.assert_called_once()

    @pytest.mark.django_db
    def test_concurrent_report_dedup(self, tenant, api_client):
        """RF-002: Same period → deduplicated."""
        payload = {
            "report_type": "weekly_outlook",
            "period_start": "2026-04-13",
            "period_end": "2026-04-19",
        }

        response1 = api_client.post("/api/reports/reports/", payload, format="json")
        response2 = api_client.post("/api/reports/reports/", payload, format="json")

        assert response1.status_code in [200, 201, 202]
        assert response2.status_code in [200, 202]

        # Same report ID returned
        assert response1.json()["id"] == response2.json()["id"]

    @pytest.mark.django_db
    def test_report_model_exists(self, tenant):
        """Verify Report model can be instantiated."""
        from reports.models import Report

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
        )

        assert report.id is not None
        assert report.status == Report.Status.PENDING

    @pytest.mark.django_db
    def test_report_get_detail(self, tenant, api_client):
        """GET /api/reports/{id}/ returns report details."""
        from reports.models import Report

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            status=Report.Status.READY,
        )

        response = api_client.get(f"/api/reports/reports/{report.id}/")

        assert response.status_code == 200
        assert response.json()["id"] == str(report.id)

    @pytest.mark.django_db
    def test_failed_report_retry(self, tenant, api_client, mocker):
        """Failed reports can be retried."""
        from reports.models import Report

        mock_task = mocker.patch("reports.views.generate_report_task.delay")
        mock_task.return_value.id = "test-task-id"

        report = Report.objects.create(
            tenant=tenant,
            report_type=Report.ReportType.WEEKLY_OUTLOOK,
            period_start=date(2026, 4, 13),
            period_end=date(2026, 4, 19),
            status=Report.Status.FAILED,
            error_message="Test failure",
        )

        response = api_client.post(f"/api/reports/reports/{report.id}/retry/")

        assert response.status_code == 202
        report.refresh_from_db()
        assert report.status == Report.Status.PENDING
        mock_task.assert_called_once()
