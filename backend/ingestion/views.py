import os
import tempfile

from celery.result import AsyncResult
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FeedbackItem, Source
from .serializers import (
    FeedbackItemListSerializer,
    FeedbackItemSerializer,
    SourceSerializer,
)
from .tasks import parse_uploaded_feedback_file


class FeedbackItemPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SourceViewSet(viewsets.ModelViewSet):
    serializer_class = SourceSerializer

    def get_queryset(self):
        # TenantManager auto-filters by request.tenant via contextvar
        return Source.objects.all().order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


class FeedbackItemViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackItemSerializer
    pagination_class = FeedbackItemPagination

    def get_serializer_class(self):
        if self.action == "list":
            return FeedbackItemListSerializer
        return FeedbackItemSerializer

    def get_queryset(self):
        qs = FeedbackItem.objects.select_related("source").order_by("-received_at")

        sentiment = self.request.query_params.get("sentiment")
        if sentiment:
            qs = qs.filter(sentiment=sentiment)

        urgency = self.request.query_params.get("urgency")
        if urgency:
            qs = qs.filter(urgency=urgency)

        source = self.request.query_params.get("source")
        if source:
            qs = qs.filter(source_id=source)

        theme = self.request.query_params.get("theme")
        if theme:
            qs = qs.filter(themes__contains=[theme])

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(content__icontains=search)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(received_at__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(received_at__lte=date_to)

        return qs


class UploadFeedbackFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, source_id: str):
        upload = request.FILES.get("file")

        if upload is None:
            return Response(
                {"detail": "file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TenantManager scopes this lookup to request.tenant
        source = get_object_or_404(Source, id=source_id)

        extension = os.path.splitext(upload.name)[1].lower()
        requested_format = str(request.data.get("file_format", "")).lower().strip()
        file_format = requested_format or ("jsonl" if extension == ".jsonl" else "csv")
        if file_format not in {"csv", "jsonl"}:
            return Response(
                {"detail": "file_format must be one of: csv, jsonl."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=f".{file_format}", delete=False
        ) as temp_file:
            for chunk in upload.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        task = parse_uploaded_feedback_file.delay(
            source_id=str(source.id),
            file_path=temp_file_path,
            file_format=file_format,
        )

        source_config = dict(source.config or {})
        source_config.update(
            {
                "ingestion_status": "pending",
                "ingestion_task_id": task.id,
                "ingestion_original_filename": upload.name,
            }
        )
        source.config = source_config
        source.save(update_fields=["config"])

        return Response(
            {
                "task_id": task.id,
                "source_id": str(source.id),
                "status": "pending",
                "message": "Upload accepted. Poll task status for progress.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class WebhookFeedbackView(APIView):
    """Receives a single feedback item via webhook POST."""

    def post(self, request, source_id: str):
        source = get_object_or_404(Source, id=source_id)

        data = request.data
        content = data.get("content") or data.get("text") or data.get("message")
        if not content:
            return Response(
                {"detail": "content (or text/message) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        received_at_raw = data.get("received_at") or data.get("timestamp")
        received_at = None
        if received_at_raw:
            received_at = parse_datetime(str(received_at_raw))
        if received_at is None:
            received_at = timezone.now()

        item = FeedbackItem.objects.create(
            tenant=request.tenant,
            source=source,
            external_id=data.get("external_id") or data.get("id"),
            content=content,
            author=data.get("author") or data.get("user"),
            metadata=data,
            received_at=received_at,
        )

        return Response(
            {
                "id": str(item.id),
                "source_id": str(source.id),
                "status": "received",
            },
            status=status.HTTP_201_CREATED,
        )


class IngestionTaskStatusView(APIView):
    def get(self, request, task_id: str):
        task_result = AsyncResult(task_id)

        payload = {
            "task_id": task_id,
            "status": task_result.status.lower(),
        }

        if task_result.successful():
            payload["result"] = task_result.result
        elif task_result.failed():
            payload["error"] = str(task_result.result)

        return Response(payload, status=status.HTTP_200_OK)
