from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id",
            "alert_type",
            "severity",
            "title",
            "description",
            "metadata",
            "acknowledged",
            "created_at",
        ]
        read_only_fields = fields

from rest_framework import serializers

from .models import TrendSnapshot


class TrendSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendSnapshot
        fields = ["id", "snapshot_date", "metrics", "created_at"]
