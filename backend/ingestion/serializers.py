from rest_framework import serializers
from .models import Source, FeedbackItem, RoutingConfig


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "name", "source_type", "config", "last_synced_at", "created_at"]
        read_only_fields = ["id", "created_at"]


class FeedbackItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackItem
        fields = [
            "id",
            "source",
            "external_id",
            "content",
            "author",
            "metadata",
            "received_at",
            "created_at",
            "sentiment",
            "sentiment_confidence",
            "urgency",
            "themes",
            "ai_summary",
            "embedding",
            "processed_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "sentiment",
            "sentiment_confidence",
            "urgency",
            "themes",
            "ai_summary",
            "embedding",
            "processed_at",
        ]


class FeedbackItemListSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = FeedbackItem
        fields = [
            "id",
            "source",
            "source_name",
            "content",
            "author",
            "sentiment",
            "sentiment_confidence",
            "urgency",
            "themes",
            "ai_summary",
            "received_at",
            "processed_at",
        ]


class RoutingConfigSerializer(serializers.ModelSerializer):
    flagged_preview_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoutingConfig
        fields = [
            "id",
            "source",
            "confidence_threshold",
            "items_below_threshold_action",
            "updated_at",
            "flagged_preview_count",
        ]
        read_only_fields = ["id", "source", "updated_at", "flagged_preview_count"]
