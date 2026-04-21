"""
Report serializers.
"""

from rest_framework import serializers

from reports.models import Report, ReportSection


class ReportSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSection
        fields = [
            "id",
            "section_type",
            "order",
            "raw_content",
            "polished_content",
        ]
        read_only_fields = fields


class ReportSerializer(serializers.ModelSerializer):
    sections = ReportSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "report_type",
            "period_start",
            "period_end",
            "status",
            "raw_data",
            "polished_content",
            "error_message",
            "generated_at",
            "created_at",
            "sections",
        ]
        read_only_fields = [
            "id",
            "status",
            "raw_data",
            "polished_content",
            "error_message",
            "generated_at",
            "created_at",
            "sections",
        ]


class ReportCreateSerializer(serializers.Serializer):
    """Serializer for creating a new report."""

    report_type = serializers.ChoiceField(
        choices=Report.ReportType.choices,
        default=Report.ReportType.WEEKLY_OUTLOOK,
    )
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)

    def validate(self, data):
        from datetime import date, timedelta

        if not data.get("period_start") or not data.get("period_end"):
            today = date.today()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            last_sunday = last_monday + timedelta(days=6)
            data["period_start"] = last_monday
            data["period_end"] = last_sunday

        return data


class ReportSummarySerializer(serializers.Serializer):
    """Serializer for report summary (shared with dashboard)."""

    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_items = serializers.IntegerField()
    volume_change = serializers.FloatField(allow_null=True)
    accuracy = serializers.FloatField()
    accuracy_change = serializers.FloatField(allow_null=True)
    alerts_count = serializers.IntegerField()
