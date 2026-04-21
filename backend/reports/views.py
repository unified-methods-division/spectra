"""
Report API views.

INV-007: Report generation never blocks request thread.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.middleware import get_current_tenant
from reports.models import Report
from reports.serializers import (
    ReportSerializer,
    ReportCreateSerializer,
    ReportSummarySerializer,
)
from reports.tasks import generate_report_task


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Report CRUD.

    INV-007: POST returns 202 within 500ms; generation is async.
    """

    serializer_class = ReportSerializer

    def get_queryset(self):
        tenant = get_current_tenant()
        return Report.objects.filter(tenant=tenant).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """
        Create a new report or return existing one for same period.

        Returns 202 Accepted with task_id for async generation.
        """
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = get_current_tenant()
        data = serializer.validated_data

        existing = Report.objects.filter(
            tenant=tenant,
            report_type=data["report_type"],
            period_start=data["period_start"],
            period_end=data["period_end"],
        ).first()

        if existing:
            if existing.status == Report.Status.FAILED:
                existing.status = Report.Status.PENDING
                existing.error_message = None
                existing.save()
                task = generate_report_task.delay(str(existing.id))
                existing.task_id = task.id
                existing.save(update_fields=["task_id"])

            return Response(
                ReportSerializer(existing).data,
                status=(
                    status.HTTP_200_OK
                    if existing.status == Report.Status.READY
                    else status.HTTP_202_ACCEPTED
                ),
            )

        report = Report.objects.create(
            tenant=tenant,
            report_type=data["report_type"],
            period_start=data["period_start"],
            period_end=data["period_end"],
            status=Report.Status.PENDING,
        )

        task = generate_report_task.delay(str(report.id))
        report.task_id = task.id
        report.save(update_fields=["task_id"])

        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """Get report summary (shared data model with dashboard)."""
        report = self.get_object()

        if report.status != Report.Status.READY:
            return Response(
                {"error": "Report not ready"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_data = report.raw_data or {}
        this_week = raw_data.get("this_week", {})
        delta = raw_data.get("delta")

        summary = {
            "period_start": report.period_start,
            "period_end": report.period_end,
            "total_items": this_week.get("total_items", 0),
            "volume_change": delta.get("volume_delta") if delta else None,
            "accuracy": this_week.get("accuracy", 0),
            "accuracy_change": delta.get("accuracy_delta") if delta else None,
            "alerts_count": this_week.get("alerts_count", 0),
        }

        return Response(ReportSummarySerializer(summary).data)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """Retry a failed report generation."""
        report = self.get_object()

        if report.status != Report.Status.FAILED:
            return Response(
                {"error": "Only failed reports can be retried"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report.status = Report.Status.PENDING
        report.error_message = None
        report.save()

        task = generate_report_task.delay(str(report.id))
        report.task_id = task.id
        report.save(update_fields=["task_id"])

        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_202_ACCEPTED,
        )
