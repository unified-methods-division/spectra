from rest_framework import serializers

from ingestion.models import FeedbackItem

from .models import (
    Correction,
    CorrectionDisagreement,
    GoldSetItem,
    Recommendation,
    RecommendationEvidence,
    RecommendationOutcome,
)


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


class RecommendationEvidenceSerializer(serializers.ModelSerializer):
    feedback_item_id = serializers.UUIDField(source="feedback_item.id", read_only=True)
    feedback_item_themes = serializers.SerializerMethodField()
    feedback_item_urgency = serializers.CharField(source="feedback_item.urgency", read_only=True)
    feedback_item_sentiment = serializers.CharField(
        source="feedback_item.sentiment", read_only=True
    )

    class Meta:
        model = RecommendationEvidence
        fields = [
            "id",
            "feedback_item_id",
            "feedback_item_themes",
            "feedback_item_urgency",
            "feedback_item_sentiment",
            "evidence_weight",
            "selection_reason",
            "created_at",
        ]
        read_only_fields = fields

    def get_feedback_item_themes(self, obj):
        return getattr(obj.feedback_item, "themes", None) or []


class RecommendationSerializer(serializers.ModelSerializer):
    evidence = RecommendationEvidenceSerializer(many=True, read_only=True)
    themes = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "title",
            "problem_statement",
            "proposed_action",
            "impact_score",
            "effort_score",
            "confidence",
            "priority_score",
            "decision_owner",
            "status",
            "decided_at",
            "created_at",
            "themes",
            "evidence",
        ]
        read_only_fields = fields

    def get_themes(self, obj):
        themes: set[str] = set()
        if isinstance(obj.rationale, dict):
            for t in obj.rationale.get("themes", []) or []:
                if isinstance(t, str) and t.strip():
                    themes.add(t.strip())

        # Evidence-derived themes (helps drill-down even if rationale missing)
        for ev in getattr(obj, "evidence", []).all():
            for t in (getattr(ev.feedback_item, "themes", None) or []):
                if isinstance(t, str) and t.strip():
                    themes.add(t.strip())

        return sorted(themes)


class DisagreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrectionDisagreement
        fields = [
            "id", "feedback_item", "field_corrected", "correction_ids",
            "resolution_status", "resolved_value", "resolved_at", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class DisagreementResolveSerializer(serializers.Serializer):
    resolved_value = serializers.JSONField()


class RecommendationDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            Recommendation.Status.ACCEPTED,
            Recommendation.Status.DISMISSED,
            Recommendation.Status.NEEDS_MORE_EVIDENCE,
        ]
    )
    decision_owner = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class OutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationOutcome
        fields = [
            "id", "recommendation", "measured_at", "metric_name",
            "baseline_value", "current_value", "delta", "interpretation", "created_at",
        ]
        read_only_fields = fields


class GoldSetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldSetItem
        fields = [
            "id",
            "feedback_item",
            "gold_sentiment",
            "gold_urgency",
            "gold_themes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_feedback_item(self, value):
        request = self.context.get("request")
        if request and value.tenant_id != request.tenant.id:
            raise serializers.ValidationError("Feedback item does not belong to this tenant.")
        return value


class DriftDeltaSerializer(serializers.Serializer):
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    accuracy = serializers.FloatField()
    prev_accuracy = serializers.FloatField(allow_null=True)
    delta = serializers.FloatField(allow_null=True)
