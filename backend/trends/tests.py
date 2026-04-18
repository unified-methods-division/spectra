from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from analysis.models import Correction
from core.models import Tenant
from ingestion.models import FeedbackItem, Source

from .engine import compute_daily_accuracy
from .models import TrendSnapshot
from .tasks import compute_daily_snapshots


class TenantHeaderMixin:
    """Sets X-Tenant-ID header on all requests for the active tenant."""

    def set_tenant(self, tenant):
        self.tenant = tenant
        self.client.credentials(HTTP_X_TENANT_ID=str(tenant.id))


# ===================================================================
# Cycle 1 — Accuracy Engine (existing)
# ===================================================================


class AccuracyEngineTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="T")
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="s",
            source_type=Source.SourceType.CSV_UPLOAD,
        )
        self.today = date.today()

    def _create_item(self, **kwargs):
        defaults = {
            "tenant": self.tenant,
            "source": self.source,
            "content": "x",
            "received_at": timezone.now(),
            "created_at": timezone.now(),
        }
        defaults.update(kwargs)
        return FeedbackItem.objects.create(**defaults)

    def test_accuracy_counts_ai_original_not_post_correction_value(self):
        """
        After correction, item.sentiment is 'positive' (human value).
        But the AI originally predicted 'negative'.
        Accuracy should attribute total to 'negative' (AI), not 'positive'.
        """
        item = self._create_item(
            sentiment=FeedbackItem.Sentiment.NEGATIVE,
            urgency=FeedbackItem.Urgency.MEDIUM,
        )

        Correction.objects.create(
            tenant=self.tenant,
            feedback_item=item,
            field_corrected=Correction.CorrectedField.SENTIMENT,
            ai_value="negative",
            human_value="positive",
        )
        item.sentiment = "positive"
        item.save()

        snapshot = compute_daily_accuracy(str(self.tenant.id), self.today)

        by_sent = snapshot.metrics["accuracy_by_sentiment"]
        self.assertIn("negative", by_sent)
        self.assertNotIn("positive", by_sent)
        self.assertEqual(by_sent["negative"], 0.0)


# ===================================================================
# Cycle 2 — Beat Task (compute_daily_snapshots)
# ===================================================================


class ComputeDailySnapshotsTaskTests(TestCase):
    def setUp(self):
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
        self.today = date.today()

    def test_task_creates_snapshot_for_each_tenant(self):
        """Beat task creates one TrendSnapshot per tenant for today."""
        now = timezone.now()
        FeedbackItem.objects.create(
            tenant=self.tenant_a,
            source=self.source_a,
            content="a1",
            received_at=now,
            sentiment=FeedbackItem.Sentiment.POSITIVE,
        )
        FeedbackItem.objects.create(
            tenant=self.tenant_b,
            source=self.source_b,
            content="b1",
            received_at=now,
            sentiment=FeedbackItem.Sentiment.NEGATIVE,
        )

        compute_daily_snapshots()

        self.assertEqual(TrendSnapshot.objects.count(), 2)
        snap_a = TrendSnapshot.objects.get(tenant=self.tenant_a, snapshot_date=self.today)
        snap_b = TrendSnapshot.objects.get(tenant=self.tenant_b, snapshot_date=self.today)
        self.assertIn("total_accuracy", snap_a.metrics)
        self.assertIn("total_accuracy", snap_b.metrics)

    def test_task_handles_tenant_with_no_items(self):
        """Tenant with no feedback still gets a snapshot (zero predictions)."""
        compute_daily_snapshots()

        self.assertEqual(TrendSnapshot.objects.count(), 2)
        snap = TrendSnapshot.objects.get(tenant=self.tenant_a, snapshot_date=self.today)
        self.assertEqual(snap.metrics["total_accuracy"], 0)


# ===================================================================
# Cycle 3 — Snapshot List API
# ===================================================================


class SnapshotListViewTests(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.tenant_a = Tenant.objects.create(name="Tenant A")
        self.tenant_b = Tenant.objects.create(name="Tenant B")

    def _create_snapshot(self, tenant, snapshot_date):
        return TrendSnapshot.objects.create(
            tenant=tenant,
            snapshot_date=snapshot_date,
            metrics={"total_accuracy": 0.85},
        )

    def test_returns_snapshots_ordered_by_date(self):
        """GET /api/trends/snapshots/ returns snapshots in ascending date order."""
        self.set_tenant(self.tenant_a)
        today = date.today()
        yesterday = today - timedelta(days=1)
        self._create_snapshot(self.tenant_a, today)
        self._create_snapshot(self.tenant_a, yesterday)

        response = self.client.get("/api/trends/snapshots/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 2)
        dates = [s["snapshot_date"] for s in body]
        self.assertEqual(dates, [str(yesterday), str(today)])

    def test_start_end_date_filter(self):
        """?start=&end= filters to bounded date range."""
        self.set_tenant(self.tenant_a)
        today = date.today()
        day1 = today - timedelta(days=6)
        day2 = today - timedelta(days=3)
        day3 = today
        self._create_snapshot(self.tenant_a, day1)
        self._create_snapshot(self.tenant_a, day2)
        self._create_snapshot(self.tenant_a, day3)

        response = self.client.get(
            "/api/trends/snapshots/",
            {"start": str(day2), "end": str(day2)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["snapshot_date"], str(day2))

    def test_cross_tenant_isolation(self):
        """Other tenant's snapshots are not returned."""
        self.set_tenant(self.tenant_a)
        today = date.today()
        self._create_snapshot(self.tenant_a, today)
        self._create_snapshot(self.tenant_b, today)

        response = self.client.get("/api/trends/snapshots/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 1)

    def test_unauthenticated_returns_403(self):
        """Request without X-Tenant-ID header returns 403."""
        self.client.credentials()  # Clear credentials
        response = self.client.get("/api/trends/snapshots/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
