from rest_framework import serializers

from ingestion.models import FeedbackItem

from .models import Correction


class CorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Correction
        fields = [
            "id",
            "feedback_item",
            "field_corrected",
            "ai_value",
            "human_value",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        field = attrs["field_corrected"]
        hv = attrs["human_value"]

        if field == "sentiment" and hv not in FeedbackItem.Sentiment.values:
            raise serializers.ValidationError({"human_value": "Invalid sentiment."})
        if field == "urgency" and hv not in FeedbackItem.Urgency.values:
            raise serializers.ValidationError({"human_value": "Invalid urgency."})
        if field == "themes" and (
            not isinstance(hv, list)
            or not all(isinstance(t, str) and t.strip() for t in hv)
        ):
            raise serializers.ValidationError({"human_value": "Must be list[str]."})

        return attrs
