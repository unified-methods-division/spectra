from rest_framework import serializers

from .models import TrendSnapshot


class TrendSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendSnapshot
        fields = ["id", "snapshot_date", "metrics", "created_at"]
