import uuid
from unittest.mock import MagicMock, patch

import numpy as np
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Tenant
from ingestion.models import FeedbackItem, Source
from themes.models import Theme


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIMS = 8


def _vec(seed: int) -> list[float]:
    """Deterministic unit vector for testing (low-dim so tests are fast)."""
    rng = np.random.RandomState(seed)
    v = rng.randn(DIMS)
    return (v / np.linalg.norm(v)).tolist()


def _close_vec(base: list[float], noise_scale: float = 0.05) -> list[float]:
    """Return a vector very close to *base* (cosine >= 0.95)."""
    arr = np.array(base) + np.random.RandomState(42).randn(len(base)) * noise_scale
    return (arr / np.linalg.norm(arr)).tolist()


def _far_vec(base: list[float]) -> list[float]:
    """Return a vector far from *base* (cosine ~ 0)."""
    orth = np.roll(np.array(base), 3)[::-1]
    orth[0] = -orth[0]
    return (orth / np.linalg.norm(orth)).tolist()


class TenantHeaderMixin:
    def set_tenant(self, tenant):
        self.tenant = tenant
        self.client.credentials(HTTP_X_TENANT_ID=str(tenant.id))


class DiscoveryTestBase(TestCase):
    """Shared setup for discovery-engine tests."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Acme Corp")
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="CSV Import",
            source_type=Source.SourceType.CSV_UPLOAD,
        )

    def _item(self, content="feedback", embedding=None, **kw):
        defaults = dict(
            tenant=self.tenant,
            source=self.source,
            content=content,
            received_at=timezone.now(),
            processed_at=timezone.now(),
            sentiment=FeedbackItem.Sentiment.NEGATIVE,
            sentiment_confidence=0.9,
            urgency=FeedbackItem.Urgency.MEDIUM,
            themes=["general"],
            ai_summary="stub",
        )
        defaults.update(kw)
        return FeedbackItem.objects.create(embedding=embedding, **defaults)


# ===================================================================
# Cycle 1 — Discovery engine
# ===================================================================


class DiscoverCreatesNewThemesTest(DiscoveryTestBase):
    """Given N embedded items forming 2 clusters, discovery creates 2 Themes."""

    @patch("themes.discovery.embed_texts")
    @patch("themes.discovery.summarize_cluster")
    @patch("themes.discovery.HDBSCAN")
    def test_creates_two_themes(self, mock_hdbscan, mock_summarize, mock_embed):
        from themes.discovery import ThemeSummary, discover_themes

        items = [self._item(f"item-{i}", embedding=_vec(i)) for i in range(10)]

        labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
        mock_hdbscan.return_value.fit_predict.return_value = labels

        mock_summarize.side_effect = [
            ThemeSummary(name="Billing Issues", slug="billing-issues", description="Problems with billing"),
            ThemeSummary(name="Login Errors", slug="login-errors", description="Users can't log in"),
        ]

        vec_billing = _vec(100)
        vec_login = _vec(200)
        mock_embed.return_value = [vec_billing, vec_login]

        result = discover_themes(str(self.tenant.id))

        self.assertEqual(result["themes_created"], 2)
        self.assertEqual(Theme.objects.filter(tenant=self.tenant).count(), 2)
        for theme in Theme.objects.filter(tenant=self.tenant):
            self.assertEqual(theme.source, Theme.ThemeSource.DISCOVERED)
            self.assertEqual(theme.item_count, 5)
            self.assertIsNotNone(theme.first_seen_at)
        # Explorer filters on FeedbackItem.themes JSON — slug must be written back
        for item in items[:5]:
            item.refresh_from_db()
            self.assertIn("billing-issues", item.themes or [])
        for item in items[5:]:
            item.refresh_from_db()
            self.assertIn("login-errors", item.themes or [])


class DiscoverMergesSimilarThemeTest(DiscoveryTestBase):
    """Existing theme with cosine >= 0.85 to new cluster → merge, not create."""

    @patch("themes.discovery.embed_texts")
    @patch("themes.discovery.summarize_cluster")
    @patch("themes.discovery.HDBSCAN")
    def test_merges_into_existing(self, mock_hdbscan, mock_summarize, mock_embed):
        from themes.discovery import ThemeSummary, discover_themes

        existing = Theme.objects.create(
            tenant=self.tenant,
            slug="billing-issues",
            name="Billing Issues",
            source=Theme.ThemeSource.MANUAL,
            item_count=10,
        )

        items = [self._item(f"item-{i}", embedding=_vec(i)) for i in range(6)]
        labels = np.array([0, 0, 0, 0, 0, 0])
        mock_hdbscan.return_value.fit_predict.return_value = labels

        mock_summarize.return_value = ThemeSummary(
            name="Billing Problems",
            slug="billing-problems",
            description="Issues with invoices",
        )

        base_vec = _vec(100)
        close = _close_vec(base_vec, noise_scale=0.01)
        mock_embed.side_effect = [
            [base_vec],  # new theme name embedding
            [close],     # existing theme name embedding
        ]

        result = discover_themes(str(self.tenant.id))

        self.assertEqual(result["themes_created"], 0)
        self.assertEqual(result["themes_merged"], 1)
        self.assertEqual(Theme.objects.filter(tenant=self.tenant).count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.item_count, 10 + 6)
        for item in items:
            item.refresh_from_db()
            self.assertIn("billing-issues", item.themes or [])

class DiscoverNoiseIgnoredTest(DiscoveryTestBase):
    """Items labeled -1 by HDBSCAN are noise and don't appear in theme counts."""

    @patch("themes.discovery.embed_texts")
    @patch("themes.discovery.summarize_cluster")
    @patch("themes.discovery.HDBSCAN")
    def test_noise_excluded(self, mock_hdbscan, mock_summarize, mock_embed):
        from themes.discovery import ThemeSummary, discover_themes

        items = [self._item(f"item-{i}", embedding=_vec(i)) for i in range(8)]

        labels = np.array([0, 0, 0, 0, 0, -1, -1, -1])
        mock_hdbscan.return_value.fit_predict.return_value = labels

        mock_summarize.return_value = ThemeSummary(
            name="Onboarding Flow", slug="onboarding-flow", description="Onboarding UX"
        )
        mock_embed.return_value = [_vec(100)]

        result = discover_themes(str(self.tenant.id))

        self.assertEqual(result["noise_items"], 3)
        theme = Theme.objects.get(tenant=self.tenant)
        self.assertEqual(theme.item_count, 5)


class DiscoverPicksClosestToCentroidTest(DiscoveryTestBase):
    """Representatives sent to LLM are the items closest to cluster centroid."""

    @patch("themes.discovery.embed_texts")
    @patch("themes.discovery.summarize_cluster")
    @patch("themes.discovery.HDBSCAN")
    def test_representative_selection(self, mock_hdbscan, mock_summarize, mock_embed):
        from themes.discovery import ThemeSummary, discover_themes

        base = np.ones(DIMS)
        base = base / np.linalg.norm(base)

        near_vec = (base + np.random.RandomState(0).randn(DIMS) * 0.01)
        near_vec = (near_vec / np.linalg.norm(near_vec)).tolist()

        def _orthogonal(seed):
            rng = np.random.RandomState(seed)
            v = rng.randn(DIMS)
            v = v - np.dot(v, base) * base
            return (v / np.linalg.norm(v)).tolist()

        near_item = self._item("near-centroid", embedding=near_vec)
        far_items = [self._item(f"far-{i}", embedding=_orthogonal(i + 10)) for i in range(5)]

        labels = np.array([0] * 6)
        mock_hdbscan.return_value.fit_predict.return_value = labels

        mock_summarize.return_value = ThemeSummary(
            name="Test Theme", slug="test-theme", description="desc"
        )
        mock_embed.return_value = [_vec(100)]

        discover_themes(str(self.tenant.id))

        call_args = mock_summarize.call_args
        rep_contents = call_args[0][0]
        self.assertIn("near-centroid", rep_contents)


class DiscoverTooFewItemsTest(DiscoveryTestBase):
    """Fewer than min_cluster_size embedded items → early return, no errors."""

    @patch("themes.discovery.HDBSCAN")
    def test_early_return(self, mock_hdbscan):
        from themes.discovery import discover_themes

        self._item("only one", embedding=_vec(0))

        result = discover_themes(str(self.tenant.id))

        mock_hdbscan.assert_not_called()
        self.assertEqual(result["themes_created"], 0)
        self.assertEqual(result["themes_merged"], 0)
        self.assertEqual(result["noise_items"], 0)


# ===================================================================
# Cycle 2 — Celery tasks
# ===================================================================


class DiscoverThemesTaskTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Task Tenant")

    @patch("themes.tasks.discover_themes")
    def test_task_calls_engine(self, mock_discover):
        from themes.tasks import discover_themes_for_tenant

        mock_discover.return_value = {"themes_created": 1, "themes_merged": 0, "noise_items": 2}

        result = discover_themes_for_tenant(str(self.tenant.id))

        mock_discover.assert_called_once_with(str(self.tenant.id))
        self.assertEqual(result["themes_created"], 1)


class DiscoverAllTenantsTaskTest(TestCase):
    @patch("themes.tasks.discover_themes_for_tenant")
    def test_fans_out_to_all_tenants(self, mock_per_tenant):
        from themes.tasks import discover_themes_for_all_tenants

        t1 = Tenant.objects.create(name="Tenant A")
        t2 = Tenant.objects.create(name="Tenant B")

        discover_themes_for_all_tenants()

        self.assertEqual(mock_per_tenant.delay.call_count, 2)
        called_ids = {c[0][0] for c in mock_per_tenant.delay.call_args_list}
        self.assertEqual(called_ids, {str(t1.id), str(t2.id)})


# ===================================================================
# Cycle 3 — Theme API
# ===================================================================


class ThemeListAPITest(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.tenant_a = Tenant.objects.create(name="Tenant A")
        self.tenant_b = Tenant.objects.create(name="Tenant B")

    def test_returns_tenant_themes_ordered_by_item_count(self):
        self.set_tenant(self.tenant_a)
        source = Source.objects.create(
            tenant=self.tenant_a,
            name="List test source",
            source_type=Source.SourceType.CSV_UPLOAD,
        )
        Theme.objects.create(tenant=self.tenant_a, slug="small", name="Small", item_count=999)
        Theme.objects.create(tenant=self.tenant_a, slug="big", name="Big", item_count=999)
        now = timezone.now()
        for i in range(50):
            FeedbackItem.objects.create(
                tenant=self.tenant_a,
                source=source,
                content=f"big-{i}",
                received_at=now,
                themes=["big"],
            )
        for i in range(5):
            FeedbackItem.objects.create(
                tenant=self.tenant_a,
                source=source,
                content=f"small-{i}",
                received_at=now,
                themes=["small"],
            )

        response = self.client.get("/api/themes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        slugs = [t["slug"] for t in body]
        self.assertEqual(slugs, ["big", "small"])
        by_slug = {t["slug"]: t["item_count"] for t in body}
        self.assertEqual(by_slug["big"], 50)
        self.assertEqual(by_slug["small"], 5)

    def test_excludes_other_tenant(self):
        Theme.objects.create(tenant=self.tenant_a, slug="a-theme", name="A Theme")
        Theme.objects.create(tenant=self.tenant_b, slug="b-theme", name="B Theme")

        self.set_tenant(self.tenant_a)
        response = self.client.get("/api/themes/")

        slugs = [t["slug"] for t in response.json()]
        self.assertIn("a-theme", slugs)
        self.assertNotIn("b-theme", slugs)


class TriggerDiscoveryAPITest(TenantHeaderMixin, APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.tenant = Tenant.objects.create(name="Trigger Tenant")

    @patch("themes.views.discover_themes_for_tenant")
    def test_returns_202(self, mock_task):
        self.set_tenant(self.tenant)
        response = self.client.post("/api/themes/discover/")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_task.delay.assert_called_once_with(str(self.tenant.id))

    def test_no_tenant_header_returns_403(self):
        response = self.client.post("/api/themes/discover/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
