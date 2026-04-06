from rest_framework import serializers
from .models import Source, FeedbackItem


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
