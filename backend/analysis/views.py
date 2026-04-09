from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import Source


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
