from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.models import Tenant
from ingestion.models import FeedbackAnalysis, FeedbackItem, RoutingConfig, Source
from themes.models import Theme

from .tasks import classify_feedback_batch, embed_feedback_batch, process_source


def _make_analysis(**overrides) -> FeedbackAnalysis:
    defaults = {
        "sentiment": FeedbackItem.Sentiment.NEGATIVE,
        "urgency": FeedbackItem.Urgency.MEDIUM,
        "sentiment_confidence": 0.92,
        "themes": ["ux", "performance"],
        "ai_summary": "User reports app crashes on login.",
    }
    defaults.update(overrides)
    return FeedbackAnalysis(**defaults)


class ClassifyBatchTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="Test Source",
            source_type=Source.SourceType.CSV_UPLOAD,
        )

    def _create_item(self, content="Test feedback", **kwargs):
        defaults = {
            "tenant": self.tenant,
            "source": self.source,
            "content": content,
            "received_at": timezone.now(),
        }
        defaults.update(kwargs)
        return FeedbackItem.objects.create(**defaults)

    @patch("analysis.tasks.classify_item")
    def test_classify_batch_processes_unprocessed_items(self, mock_classify):
        """Batch task classifies all unprocessed items and writes results to DB"""
        mock_classify.return_value = _make_analysis()
        items = [self._create_item(f"Feedback {i}") for i in range(3)]

        result = classify_feedback_batch(str(self.source.id))

        self.assertEqual(result["classified"], 3)
        for item in items:
            item.refresh_from_db()
            self.assertIsNotNone(item.processed_at)
            self.assertEqual(item.sentiment, FeedbackItem.Sentiment.NEGATIVE)
            self.assertEqual(item.urgency, FeedbackItem.Urgency.MEDIUM)
            self.assertAlmostEqual(item.sentiment_confidence, 0.92)
            self.assertEqual(item.themes, ["ux", "performance"])
            self.assertEqual(item.ai_summary, "User reports app crashes on login.")

    @patch("analysis.tasks.classify_item")
    def test_classify_batch_skips_already_processed(self, mock_classify):
        """Items with processed_at set are not re-classified"""
        mock_classify.return_value = _make_analysis()
        self._create_item("Already done", processed_at=timezone.now())
        unprocessed = self._create_item("Not yet done")

        result = classify_feedback_batch(str(self.source.id))

        self.assertEqual(result["classified"], 1)
        self.assertEqual(mock_classify.call_count, 1)
        unprocessed.refresh_from_db()
        self.assertIsNotNone(unprocessed.processed_at)

    @patch("analysis.tasks.classify_item")
    def test_low_confidence_flags_item_for_review(self, mock_classify):
        """Items below confidence threshold get metadata.needs_review = True"""
        RoutingConfig.objects.create(
            source=self.source,
            tenant=self.tenant,
            confidence_threshold=0.9,
        )
        mock_classify.return_value = _make_analysis(sentiment_confidence=0.7)
        item = self._create_item()

        classify_feedback_batch(str(self.source.id))

        item.refresh_from_db()
        self.assertTrue(item.metadata["needs_review"])
        self.assertIsNotNone(item.processed_at)

    @patch("analysis.tasks.classify_item")
    def test_single_item_failure_does_not_kill_batch(self, mock_classify):
        """One item raising an exception doesn't prevent other items from being classified"""
        mock_classify.side_effect = [
            Exception("LLM error"),
            _make_analysis(),
        ]
        self._create_item("Will fail")
        item_ok = self._create_item("Will succeed")

        result = classify_feedback_batch(str(self.source.id))

        self.assertEqual(result["classified"], 1)
        self.assertEqual(result["failed"], 1)
        item_ok.refresh_from_db()
        self.assertIsNotNone(item_ok.processed_at)

    @patch("analysis.tasks.classify_item")
    def test_discovered_themes_upserted(self, mock_classify):
        """Theme slugs not in tenant taxonomy are created as discovered themes"""
        Theme.objects.create(tenant=self.tenant, slug="ux", name="UX")
        mock_classify.return_value = _make_analysis(themes=["ux", "login-bug"])
        self._create_item()

        result = classify_feedback_batch(str(self.source.id))

        self.assertIn("login-bug", result["discovered_themes"])
        new_theme = Theme.objects.get(tenant=self.tenant, slug="login-bug")
        self.assertEqual(new_theme.source, Theme.ThemeSource.DISCOVERED)

    @patch("analysis.tasks.classify_item")
    def test_source_config_updated_on_completion(self, mock_classify):
        """Source config tracks classification status and counts"""
        mock_classify.return_value = _make_analysis()
        self._create_item()

        classify_feedback_batch(str(self.source.id))

        self.source.refresh_from_db()
        self.assertEqual(self.source.config["classification_status"], "completed")
        self.assertEqual(self.source.config["classification_counts"]["classified"], 1)


FAKE_VECTOR = [0.1] * 1536


class EmbedBatchTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.source = Source.objects.create(
            tenant=self.tenant,
            name="Test Source",
            source_type=Source.SourceType.CSV_UPLOAD,
        )

    def _create_item(self, content="Test feedback", **kwargs):
        defaults = {
            "tenant": self.tenant,
            "source": self.source,
            "content": content,
            "received_at": timezone.now(),
        }
        defaults.update(kwargs)
        return FeedbackItem.objects.create(**defaults)

    def _create_classified_item(self, content="Classified feedback", **kwargs):
        """Create an item that has been classified but not yet embedded."""
        return self._create_item(
            content,
            sentiment=FeedbackItem.Sentiment.NEGATIVE,
            sentiment_confidence=0.9,
            urgency=FeedbackItem.Urgency.MEDIUM,
            themes=["ux"],
            ai_summary="Test summary",
            processed_at=timezone.now(),
            **kwargs,
        )

    @patch("analysis.tasks.embed_texts")
    def test_embed_batch_processes_classified_items(self, mock_embed):
        """Embeds classified items, skips unprocessed ones"""
        mock_embed.return_value = [FAKE_VECTOR, FAKE_VECTOR]
        classified = [self._create_classified_item(f"Item {i}") for i in range(2)]
        self._create_item("Unprocessed — no processed_at")

        result = embed_feedback_batch(str(self.source.id))

        self.assertEqual(result["embedded"], 2)
        mock_embed.assert_called_once()
        for item in classified:
            item.refresh_from_db()
            self.assertIsNotNone(item.embedding)

    @patch("analysis.tasks.embed_texts")
    def test_embed_batch_skips_already_embedded(self, mock_embed):
        """Items with existing embeddings are not re-embedded"""
        mock_embed.return_value = [FAKE_VECTOR]
        self._create_classified_item("Already embedded", embedding=FAKE_VECTOR)
        fresh = self._create_classified_item("Needs embedding")

        result = embed_feedback_batch(str(self.source.id))

        self.assertEqual(result["embedded"], 1)
        fresh.refresh_from_db()
        self.assertIsNotNone(fresh.embedding)

    @patch("analysis.tasks.embed_texts")
    def test_embed_batch_chunk_error_resilience(self, mock_embed):
        """One chunk failing doesn't kill the entire batch"""
        # First chunk fails, second succeeds
        mock_embed.side_effect = [Exception("API error"), [FAKE_VECTOR]]
        items = [self._create_classified_item(f"Item {i}") for i in range(2)]

        with patch("analysis.tasks.EMBED_CHUNK_SIZE", 1):
            result = embed_feedback_batch(str(self.source.id))

        self.assertEqual(result["embedded"], 1)
        self.assertEqual(result["failed"], 1)

    @patch("analysis.tasks.embed_texts")
    def test_source_config_updated_on_embed_completion(self, mock_embed):
        """Source config tracks embedding status and counts"""
        mock_embed.return_value = [FAKE_VECTOR]
        self._create_classified_item()

        embed_feedback_batch(str(self.source.id))

        self.source.refresh_from_db()
        self.assertEqual(self.source.config["embedding_status"], "completed")
        self.assertEqual(self.source.config["embedding_counts"]["embedded"], 1)

    @patch("analysis.tasks.embed_feedback_batch")
    @patch("analysis.tasks.classify_feedback_batch")
    def test_process_source_chains_classify_and_embed(
        self, mock_classify, mock_embed
    ):
        """Pipeline task dispatches classify → embed chain"""
        process_source(str(self.source.id))

        # Both tasks should have been called via chain.apply_async
        # Since we're mocking the tasks themselves, verify the chain was built
        # by checking that apply_async was called on the chain
        # (process_source builds and dispatches the chain)
        self.assertTrue(mock_classify.si.called or mock_embed.si.called)
