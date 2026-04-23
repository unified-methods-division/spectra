from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import Source

from .models import Recommendation
from .serializers import (
    CorrectionSerializer,
    RecommendationDecisionSerializer,
    RecommendationSerializer,
)


class ProcessingStatusView(APIView):
    """GET combined classification + embedding progress for a source."""

    def get(self, request, source_id: str):
        source = get_object_or_404(Source, id=source_id)
        config = source.config or {}

        classification = {
            "status": config.get("classification_status"),
            "counts": config.get("classification_counts"),
            "error": config.get("classification_error"),
        }
        embedding = {
            "status": config.get("embedding_status"),
            "counts": config.get("embedding_counts"),
            "error": config.get("embedding_error"),
        }

        # Derive overall status
        statuses = [classification["status"], embedding["status"]]
        if "failed" in statuses:
            overall = "failed"
        elif "processing" in statuses:
            overall = "processing"
        elif all(s == "completed" for s in statuses):
            overall = "completed"
        else:
            overall = "pending"

        return Response(
            {
                "source_id": str(source.id),
                "classification": classification,
                "embedding": embedding,
                "overall_status": overall,
            },
            status=status.HTTP_200_OK,
        )


class CorrectionCreateView(CreateAPIView):
    serializer_class = CorrectionSerializer

    def perform_create(self, serializer):
        from django.db import transaction
        from ingestion.models import FeedbackItem

        with transaction.atomic():
            correction = serializer.save(tenant=self.request.tenant)
            FeedbackItem.objects.filter(pk=correction.feedback_item_id).update(
                **{correction.field_corrected: correction.human_value}
            )


@api_view(["GET"])
def recommendation_list(request):
    """List recommendations for current tenant."""
    qs = Recommendation.objects.filter(tenant=request.tenant).order_by("-created_at")
    status_filter = request.query_params.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return Response(RecommendationSerializer(qs, many=True).data)


@api_view(["GET"])
def recommendation_detail(request, recommendation_id: str):
    """Fetch a recommendation with evidence for drill-down."""
    rec = get_object_or_404(
        Recommendation.objects.select_related("tenant").prefetch_related(
            "evidence__feedback_item"
        ),
        tenant=request.tenant,
        id=recommendation_id,
    )
    return Response(RecommendationSerializer(rec).data)


@api_view(["POST"])
def recommendation_decide(request, recommendation_id: str):
    """
    Decision transition endpoint.

    Allowed: proposed -> accepted|dismissed|needs_more_evidence
    """
    rec = get_object_or_404(
        Recommendation.objects.filter(tenant=request.tenant),
        id=recommendation_id,
    )

    serializer = RecommendationDecisionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    next_status = serializer.validated_data["status"]
    owner = serializer.validated_data.get("decision_owner")

    from django.utils import timezone

    was_proposed = rec.status == Recommendation.Status.PROPOSED
    rec.status = next_status
    rec.decision_owner = owner if owner not in ("", None) else None
    if was_proposed:
        rec.decided_at = timezone.now()
    rec.save(update_fields=["status", "decision_owner", "decided_at"])

    rec = Recommendation.objects.prefetch_related("evidence__feedback_item").get(id=rec.id)
    return Response(RecommendationSerializer(rec).data, status=status.HTTP_200_OK)
