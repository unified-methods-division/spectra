from datetime import date, timedelta

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from core.middleware import get_current_tenant
from .models import TrendSnapshot
from .serializers import TrendSnapshotSerializer


class SnapshotListView(ListAPIView):
    serializer_class = TrendSnapshotSerializer

    def get_queryset(self):
        qs = TrendSnapshot.objects.filter(tenant=self.request.tenant).order_by(
            "snapshot_date"
        )
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")
        if start:
            qs = qs.filter(snapshot_date__gte=start)
        if end:
            qs = qs.filter(snapshot_date__lte=end)
        return qs


@api_view(["GET"])
def dashboard_summary(request):
    """
    Get dashboard summary for a period.

    INV-010: Uses same synthesis as reports for identical metrics.

    Query params:
        period: "this-week" | "last-week" | custom ISO dates
        period_start: ISO date (if period is custom)
        period_end: ISO date (if period is custom)
    """
    tenant = get_current_tenant()

    period = request.query_params.get("period", "this-week")

    if period == "this-week":
        today = date.today()
        days_since_monday = today.weekday()
        period_start = today - timedelta(days=days_since_monday)
        period_end = period_start + timedelta(days=6)
    elif period == "last-week":
        today = date.today()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday + 7)
        period_start = last_monday
        period_end = last_monday + timedelta(days=6)
    else:
        try:
            period_start = date.fromisoformat(request.query_params.get("period_start"))
            period_end = date.fromisoformat(request.query_params.get("period_end"))
        except (TypeError, ValueError):
            return Response(
                {
                    "error": "Invalid period. Use 'this-week', 'last-week', or provide period_start and period_end."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    from reports.models import Report
    from reports.services.synthesis import synthesize_report_data

    existing_report = Report.objects.filter(
        tenant=tenant,
        report_type=Report.ReportType.WEEKLY_OUTLOOK,
        period_start=period_start,
        period_end=period_end,
        status=Report.Status.READY,
    ).first()

    if existing_report and existing_report.raw_data:
        raw_data = existing_report.raw_data
        this_week = raw_data.get("this_week", {})
        delta = raw_data.get("delta")

        summary = {
            "period_start": period_start,
            "period_end": period_end,
            "total_items": this_week.get("total_items", 0),
            "volume_change": delta.get("volume_delta") if delta else None,
            "accuracy": this_week.get("accuracy", 0),
            "accuracy_change": delta.get("accuracy_delta") if delta else None,
            "alerts_count": this_week.get("alerts_count", 0),
            "source": "report",
            "report_id": str(existing_report.id),
        }
    else:
        synthesis = synthesize_report_data(
            tenant_id=str(tenant.id),
            period_start=period_start,
            period_end=period_end,
        )

        summary = {
            "period_start": period_start,
            "period_end": period_end,
            "total_items": synthesis.this_week.total_items,
            "volume_change": synthesis.delta.volume_delta if synthesis.delta else None,
            "accuracy": synthesis.this_week.accuracy,
            "accuracy_change": synthesis.delta.accuracy_delta if synthesis.delta else None,
            "alerts_count": synthesis.this_week.alerts_count,
            "source": "live",
            "report_id": None,
        }

    return Response(summary)
