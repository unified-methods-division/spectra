from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Tenant
from ingestion.models import Source


class UploadIngestionTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="CSV Upload Source",
            source_type=Source.SourceType.CSV_UPLOAD,
            config={},
        )

    @patch("ingestion.views.parse_uploaded_feedback_file.delay")
    def test_upload_endpoint_returns_202_and_enqueues_celery_task(self, mock_delay):
        mock_delay.return_value = Mock(id="task-123")

        upload = SimpleUploadedFile(
            "feedback.csv",
            b"content,author\nGreat app!,alice\n",
            content_type="text/csv",
        )

        response = self.client.post(
            reverse("upload-feedback-file", args=[str(self.source.id)]),
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["task_id"], "task-123")
        self.assertEqual(response.data["source_id"], str(self.source.id))
        self.assertEqual(response.data["status"], "pending")

        mock_delay.assert_called_once()
        call_kwargs = mock_delay.call_args.kwargs
        self.assertEqual(call_kwargs["source_id"], str(self.source.id))
        self.assertEqual(call_kwargs["file_format"], "csv")
        self.assertTrue(call_kwargs["file_path"].endswith(".csv"))

        self.source.refresh_from_db()
        self.assertEqual(self.source.config["ingestion_status"], "pending")
        self.assertEqual(self.source.config["ingestion_task_id"], "task-123")
        self.assertEqual(
            self.source.config["ingestion_original_filename"],
            "feedback.csv",
        )

    @patch("ingestion.views.AsyncResult")
    def test_task_status_endpoint_returns_task_result(self, mock_async_result):
        task_result = Mock()
        task_result.status = "SUCCESS"
        task_result.successful.return_value = True
        task_result.failed.return_value = False
        task_result.result = {"created_count": 1, "skipped_count": 0}
        mock_async_result.return_value = task_result

        response = self.client.get(reverse("ingestion-task-status", args=["task-123"]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_id"], "task-123")
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(
            response.data["result"], {"created_count": 1, "skipped_count": 0}
        )
