from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Tenant
from ingestion.models import FeedbackItem, Source


class TenantHeaderMixin:
    """Sets X-Tenant-ID header on all requests for the active tenant."""

    def set_tenant(self, tenant):
        self.tenant = tenant
        self.client.credentials(HTTP_X_TENANT_ID=str(tenant.id))


class TenantMiddlewareTests(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.tenant = Tenant.objects.create(name="Test Tenant")

    def test_request_without_tenant_header_returns_403(self):
        """Middleware rejects request with no X-Tenant-ID → 403"""
        response = self.client.get(reverse("sources-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("X-Tenant-ID", response.json()["detail"])

    def test_request_with_invalid_tenant_returns_403(self):
        """Middleware rejects request with nonexistent tenant → 403"""
        self.client.credentials(
            HTTP_X_TENANT_ID="00000000-0000-0000-0000-000000000000"
        )
        response = self.client.get(reverse("sources-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_request_with_valid_tenant_succeeds(self):
        """Middleware passes request with valid tenant → 200"""
        self.set_tenant(self.tenant)
        response = self.client.get(reverse("sources-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TenantIsolationTests(TenantHeaderMixin, APITestCase):
    """Tenant A cannot see tenant B's data."""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.tenant_a = Tenant.objects.create(name="Tenant A")
        self.tenant_b = Tenant.objects.create(name="Tenant B")

        self.source_a = Source.objects.create(
            tenant=self.tenant_a,
            name="Source A",
            source_type=Source.SourceType.CSV_UPLOAD,
        )
        self.source_b = Source.objects.create(
            tenant=self.tenant_b,
            name="Source B",
            source_type=Source.SourceType.CSV_UPLOAD,
        )

        from django.utils import timezone

        self.item_a = FeedbackItem.objects.create(
            tenant=self.tenant_a,
            source=self.source_a,
            content="Feedback from A",
            received_at=timezone.now(),
        )
        self.item_b = FeedbackItem.objects.create(
            tenant=self.tenant_b,
            source=self.source_b,
            content="Feedback from B",
            received_at=timezone.now(),
        )

    def test_tenant_a_sees_only_own_sources(self):
        """GET /sources as tenant A → only A's sources returned"""
        self.set_tenant(self.tenant_a)
        response = self.client.get(reverse("sources-list"))
        source_ids = [s["id"] for s in response.data]
        self.assertIn(str(self.source_a.id), source_ids)
        self.assertNotIn(str(self.source_b.id), source_ids)

    def test_tenant_b_sees_only_own_sources(self):
        """GET /sources as tenant B → only B's sources returned"""
        self.set_tenant(self.tenant_b)
        response = self.client.get(reverse("sources-list"))
        source_ids = [s["id"] for s in response.data]
        self.assertIn(str(self.source_b.id), source_ids)
        self.assertNotIn(str(self.source_a.id), source_ids)

    def test_tenant_a_sees_only_own_feedback_items(self):
        """GET /feedback-items as tenant A → only A's items returned"""
        self.set_tenant(self.tenant_a)
        response = self.client.get(reverse("feedback-items-list"))
        item_ids = [i["id"] for i in response.data]
        self.assertIn(str(self.item_a.id), item_ids)
        self.assertNotIn(str(self.item_b.id), item_ids)

    def test_tenant_a_cannot_access_tenant_b_source_by_id(self):
        """GET /sources/<B's id> as tenant A → 404"""
        self.set_tenant(self.tenant_a)
        response = self.client.get(
            reverse("sources-detail", args=[str(self.source_b.id)])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_to_other_tenants_source_returns_404(self):
        """POST upload to B's source as tenant A → 404"""
        self.set_tenant(self.tenant_a)
        upload = SimpleUploadedFile(
            "feedback.csv",
            b"content,author\ntest,alice\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("upload-feedback-file", args=[str(self.source_b.id)]),
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WebhookTests(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.tenant = Tenant.objects.create(name="Webhook Tenant")
        self.set_tenant(self.tenant)
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="Webhook Source",
            source_type=Source.SourceType.WEBHOOK,
        )

    def test_webhook_creates_feedback_item(self):
        """POST webhook payload → 201, item created with correct tenant + fields"""
        response = self.client.post(
            reverse("webhook-feedback", args=[str(self.source.id)]),
            {
                "content": "The billing page is broken",
                "author": "alice",
                "external_id": "ticket-42",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["source_id"], str(self.source.id))

        item = FeedbackItem.objects.get(id=response.data["id"])
        self.assertEqual(item.content, "The billing page is broken")
        self.assertEqual(item.tenant_id, self.tenant.id)
        self.assertEqual(item.external_id, "ticket-42")

    def test_webhook_without_content_returns_400(self):
        """POST webhook with no content field → 400"""
        response = self.client.post(
            reverse("webhook-feedback", args=[str(self.source.id)]),
            {"author": "alice"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_to_other_tenants_source_returns_404(self):
        """POST webhook to another tenant's source → 404"""
        other_tenant = Tenant.objects.create(name="Other")
        other_source = Source.objects.create(
            tenant=other_tenant,
            name="Other Source",
            source_type=Source.SourceType.WEBHOOK,
        )
        response = self.client.post(
            reverse("webhook-feedback", args=[str(other_source.id)]),
            {"content": "sneaky"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UploadIngestionTests(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.set_tenant(self.tenant)
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="CSV Upload Source",
            source_type=Source.SourceType.CSV_UPLOAD,
            config={},
        )

    @patch("ingestion.views.parse_uploaded_feedback_file.delay")
    def test_upload_endpoint_returns_202_and_enqueues_celery_task(self, mock_delay):
        """POST CSV upload → 202, Celery task enqueued, source config updated"""
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
        """GET task status → 200 with status + result payload"""
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
