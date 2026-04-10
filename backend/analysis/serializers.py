from rest_framework import serializers

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
