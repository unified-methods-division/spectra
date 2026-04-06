import os
import tempfile

from celery.result import AsyncResult
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FeedbackItem, Source
from .serializers import FeedbackItemSerializer, SourceSerializer
from .tasks import parse_uploaded_feedback_file


class SourceViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all().order_by("-created_at")
    serializer_class = SourceSerializer


class FeedbackItemViewSet(viewsets.ModelViewSet):
    queryset = FeedbackItem.objects.all().order_by("-received_at")
    serializer_class = FeedbackItemSerializer


class UploadFeedbackFileView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        source_id = request.data.get("source_id")
        upload = request.FILES.get("file")

        if not source_id:
            return Response(
                {"detail": "source_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if upload is None:
            return Response(
                {"detail": "file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
