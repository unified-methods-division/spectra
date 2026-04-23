from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from analysis.models import Correction, GoldSetItem, Recommendation, RecommendationEvidence
from core.models import Tenant
from ingestion.models import FeedbackItem, Source
from reports.models import Report
from trends.models import Alert


FIXTURE_PATH = Path(__file__).resolve().parent.parent.parent / "scripts" / "fixtures" / "slack_reviews.json"


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="Acme Corp")


class TestScrapeReviews:
    def test_scrape_returns_normalized_reviews(self):
        from core.management.commands.seed_real_data import _scrape_reviews

        fake_result = (
            [
                {
                    "reviewId": "gp:abc123",
                    "content": "Great app",
                    "userName": "Alice",
                    "at": datetime(2026, 4, 10, 12, 0, 0),
                    "score": 5,
                }
            ],
            None,
        )
        with patch(
            "core.management.commands.seed_real_data.reviews",
            return_value=fake_result,
        ) as mock_reviews:
            with patch(
                "core.management.commands.seed_real_data.Sort", MagicMock(NEWEST="newest")
            ):
                result = _scrape_reviews("com.Slack", count=50)

        mock_reviews.assert_called_once_with(
            "com.Slack", lang="en", country="us", sort="newest", count=50
        )
        assert len(result) == 1
        assert result[0]["reviewId"] == "gp:abc123"
        assert result[0]["content"] == "Great app"
        assert result[0]["userName"] == "Alice"
        assert result[0]["score"] == 5


class TestLoadFixture:
    def test_load_fixture_from_json(self, tmp_path):
        from core.management.commands.seed_real_data import _load_fixture

        fixture_data = [
            {
                "reviewId": "gp:1",
                "content": "Slack is great",
                "userName": "Bob",
                "at": "2026-04-10T10:00:00Z",
                "score": 4,
            }
        ]
        fixture_file = tmp_path / "reviews.json"
        fixture_file.write_text(json.dumps(fixture_data))

        result = _load_fixture(str(fixture_file))
        assert len(result) == 1
        assert result[0]["reviewId"] == "gp:1"
        assert result[0]["content"] == "Slack is great"

    def test_load_fixture_missing_file_raises(self):
        from core.management.commands.seed_real_data import _load_fixture

        with pytest.raises(FileNotFoundError):
            _load_fixture("/nonexistent/path.json")


class TestCreateSourceAndItems:
    def test_creates_source_and_bulk_creates_items(self, tenant):
        from core.management.commands.seed_real_data import _create_source_and_items

        reviews = [
            {
                "reviewId": "gp:1",
                "content": "Love it",
                "userName": "User1",
                "at": "2026-04-10T10:00:00Z",
                "score": 5,
            },
            {
                "reviewId": "gp:2",
                "content": "Terrible",
                "userName": "User2",
                "at": "2026-04-11T11:00:00Z",
                "score": 1,
            },
        ]

        source, count = _create_source_and_items(
            tenant, reviews, source_name="Google Play: com.Slack"
        )

        assert count == 2
        assert Source.objects.filter(tenant=tenant, name="Google Play: com.Slack").count() == 1
        assert FeedbackItem.objects.filter(source=source).count() == 2

        item1 = FeedbackItem.objects.get(external_id="gp:1")
        assert item1.content == "Love it"
        assert item1.author == "User1"
        assert item1.metadata == {"score": 5}

    def test_update_or_create_idempotent(self, tenant):
        from core.management.commands.seed_real_data import _create_source_and_items

        reviews = [
            {
                "reviewId": "gp:1",
                "content": "Love it",
                "userName": "User1",
                "at": "2026-04-10T10:00:00Z",
                "score": 5,
            },
        ]
        _create_source_and_items(tenant, reviews, source_name="Google Play: com.Slack")
        source2, count2 = _create_source_and_items(
            tenant, reviews, source_name="Google Play: com.Slack"
        )

        assert Source.objects.filter(tenant=tenant, name="Google Play: com.Slack").count() == 1
        assert count2 == 0

    def test_ignore_conflicts_on_duplicate_external_id(self, tenant):
        from core.management.commands.seed_real_data import _create_source_and_items

        reviews = [
            {
                "reviewId": "gp:1",
                "content": "Love it",
                "userName": "User1",
                "at": "2026-04-10T10:00:00Z",
                "score": 5,
            },
        ]
        _create_source_and_items(tenant, reviews, source_name="Google Play: com.Slack")

        reviews_updated = [
            {
                "reviewId": "gp:1",
                "content": "Love it updated",
                "userName": "User1",
                "at": "2026-04-10T10:00:00Z",
                "score": 5,
            },
            {
                "reviewId": "gp:2",
                "content": "New review",
                "userName": "User2",
                "at": "2026-04-12T10:00:00Z",
                "score": 3,
            },
        ]
        source, count = _create_source_and_items(
            tenant, reviews_updated, source_name="Google Play: com.Slack"
        )

        total = FeedbackItem.objects.filter(source=source).count()
        assert total == 2
        assert count == 1


class TestRunPipelineSync:
    @patch("core.management.commands.seed_real_data.discover_themes_for_source")
    @patch("core.management.commands.seed_real_data.embed_feedback_batch")
    @patch("core.management.commands.seed_real_data.classify_feedback_batch")
    def test_calls_all_three_tasks(self, mock_classify, mock_embed, mock_discover):
        from core.management.commands.seed_real_data import _run_pipeline_sync

        mock_classify.apply = MagicMock(return_value=MagicMock())
        mock_embed.apply = MagicMock(return_value=MagicMock())
        mock_discover.apply = MagicMock(return_value=MagicMock())

        with patch("django.test.override_settings"):
            _run_pipeline_sync("source-uuid-here")

        mock_classify.apply.assert_called_once_with(args=("source-uuid-here",))
        mock_embed.apply.assert_called_once_with(args=("source-uuid-here",))
        mock_discover.apply.assert_called_once_with(args=("source-uuid-here",))


class TestHandleCommand:
    @patch("core.management.commands.seed_real_data._run_pipeline_sync")
    @patch("core.management.commands.seed_real_data._create_source_and_items")
    @patch("core.management.commands.seed_real_data._scrape_reviews")
    def test_handle_with_tenant_id(
        self, mock_scrape, mock_create, mock_pipeline, tenant, settings
    ):
        from io import StringIO

        mock_scrape.return_value = [
            {
                "reviewId": "gp:1",
                "content": "Ok app",
                "userName": "X",
                "at": "2026-04-10T10:00:00Z",
                "score": 3,
            },
        ]
        mock_create.return_value = (MagicMock(), 1)

        out = StringIO()
        with patch("django.test.override_settings"):
            call_command(
                "seed_real_data",
                tenant_id=str(tenant.id),
                app_id="com.Slack",
                count=10,
                fixture=None,
                period_start=None,
                period_end=None,
                stdout=out,
            )

        mock_scrape.assert_called_once_with("com.Slack", 10)
        mock_create.assert_called_once()
        mock_pipeline.assert_called_once()

    @patch("core.management.commands.seed_real_data._run_pipeline_sync")
    @patch("core.management.commands.seed_real_data._create_source_and_items")
    @patch("core.management.commands.seed_real_data._load_fixture")
    def test_handle_with_fixture_flag(
        self, mock_fixture, mock_create, mock_pipeline, tenant, settings
    ):
        from io import StringIO

        mock_fixture.return_value = [
            {
                "reviewId": "gp:1",
                "content": "From file",
                "userName": "Y",
                "at": "2026-04-10T10:00:00Z",
                "score": 2,
            },
        ]
        mock_create.return_value = (MagicMock(), 1)

        out = StringIO()
        with patch("django.test.override_settings"):
            call_command(
                "seed_real_data",
                tenant_id=str(tenant.id),
                app_id="com.Slack",
                count=10,
                fixture="/path/to/reviews.json",
                period_start=None,
                period_end=None,
                stdout=out,
            )

        mock_fixture.assert_called_once_with("/path/to/reviews.json")
        mock_create.assert_called_once()

    def test_handle_no_tenant_errors(self, db):
        from io import StringIO

        out = StringIO()
        err = StringIO()
        call_command("seed_real_data", stdout=out, stderr=err)

        output = err.getvalue()
        assert "error" in output.lower() or "no tenant" in output.lower()


class TestFixtureFile:
    def test_fixture_file_exists_and_valid_json(self):
        assert FIXTURE_PATH.exists(), f"Fixture not found at {FIXTURE_PATH}"
        data = json.loads(FIXTURE_PATH.read_text())
        assert isinstance(data, list)
        assert len(data) >= 15

        required_keys = {"reviewId", "content", "userName", "at", "score"}
        for review in data:
            assert required_keys.issubset(set(review.keys())), (
                f"Missing keys in {review.get('reviewId', 'unknown')}"
            )
            assert isinstance(review["score"], int)
            assert 1 <= review["score"] <= 5


def _make_classified_items(tenant, source, count=15):
    items = []
    for i in range(count):
        score = (i % 5) + 1
        item = FeedbackItem.objects.create(
            tenant=tenant,
            source=source,
            external_id=f"gp:test-{i}",
            content=f"Test review {i}",
            author=f"User{i}",
            received_at=timezone.now(),
            metadata={"score": score},
            sentiment="neutral" if score == 3 else ("positive" if score >= 4 else "negative"),
            urgency="medium" if 2 <= score <= 3 else ("high" if score == 1 else "low"),
            themes=["usability", "performance"] if score <= 2 else ["general"],
            processed_at=timezone.now(),
        )
        items.append(item)
    return items


class TestSeedCorrections:
    def test_creates_corrections_and_updates_feedback_items(self, tenant):
        from core.management.commands.seed_real_data import _seed_corrections

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        items = _make_classified_items(tenant, source, 15)

        count = _seed_corrections(tenant, items)

        assert Correction.objects.filter(tenant=tenant).count() == count
        assert count == 15

        for corr in Correction.objects.filter(tenant=tenant, field_corrected="sentiment"):
            item = FeedbackItem.objects.get(pk=corr.feedback_item_id)
            assert item.sentiment == corr.human_value

        for corr in Correction.objects.filter(tenant=tenant, field_corrected="urgency"):
            item = FeedbackItem.objects.get(pk=corr.feedback_item_id)
            assert item.urgency == corr.human_value

    def test_creates_enough_pattern_corrections(self, tenant):
        from core.management.commands.seed_real_data import _seed_corrections

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        items = _make_classified_items(tenant, source, 15)

        _seed_corrections(tenant, items)

        from collections import Counter
        pattern_counts = Counter()
        for corr in Correction.objects.filter(tenant=tenant):
            ai_val = tuple(corr.ai_value) if isinstance(corr.ai_value, list) else corr.ai_value
            human_val = tuple(corr.human_value) if isinstance(corr.human_value, list) else corr.human_value
            key = (corr.field_corrected, human_val, ai_val)
            pattern_counts[key] += 1

        has_threshold = any(c >= 5 for c in pattern_counts.values())
        assert has_threshold, f"No pattern with ≥5 occurrences: {dict(pattern_counts)}"


class TestSeedGoldSet:
    def test_creates_gold_set_items(self, tenant):
        from core.management.commands.seed_real_data import _seed_gold_set

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        items = _make_classified_items(tenant, source, 10)

        count = _seed_gold_set(tenant, items)

        assert GoldSetItem.objects.filter(tenant=tenant).count() == count
        assert count >= 10

        for gsi in GoldSetItem.objects.filter(tenant=tenant):
            assert gsi.gold_sentiment in ("positive", "negative", "neutral")
            assert gsi.gold_urgency in ("low", "medium", "high", "critical")
            assert isinstance(gsi.gold_themes, list)

    def test_gold_set_idempotent(self, tenant):
        from core.management.commands.seed_real_data import _seed_gold_set

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        items = _make_classified_items(tenant, source, 10)

        count1 = _seed_gold_set(tenant, items)
        count2 = _seed_gold_set(tenant, items)

        assert count1 >= 10
        assert count2 == 0
        assert GoldSetItem.objects.filter(tenant=tenant).count() == count1


class TestSeedSnapshots:
    @patch("core.management.commands.seed_real_data.compute_daily_accuracy")
    def test_creates_snapshots_for_date_range(self, mock_compute, tenant):
        from core.management.commands.seed_real_data import _seed_snapshots

        fake_snapshot = MagicMock()
        mock_compute.return_value = fake_snapshot

        count = _seed_snapshots(str(tenant.id), days=14)

        assert mock_compute.call_count == 14
        assert count == 14

        today = date.today()
        expected_dates = [today - timedelta(days=d) for d in range(14, 0, -1)]
        actual_dates = [call.args[1] for call in mock_compute.call_args_list]
        assert actual_dates == expected_dates

        for call_args in mock_compute.call_args_list:
            assert call_args.args[0] == str(tenant.id)


class TestSeedReportAndAlerts:
    @patch("core.management.commands.seed_real_data.generate_report_task")
    def test_creates_report_and_triggers_alerts(self, mock_task, tenant):
        from core.management.commands.seed_real_data import _seed_report_and_alerts

        mock_task.apply = MagicMock()

        Alert.objects.create(
            tenant=tenant,
            alert_type=Alert.AlertType.VOLUME_SPIKE,
            severity=Alert.Severity.WARNING,
            title="Test alert",
            description="desc",
        )

        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        with patch("django.test.override_settings"):
            report, alert_count = _seed_report_and_alerts(tenant, period_start, period_end)

        assert Report.objects.filter(tenant=tenant).count() == 1
        assert report.report_type == Report.ReportType.WEEKLY_OUTLOOK
        assert report.period_start == period_start
        assert report.period_end == period_end
        assert report.status == Report.Status.PENDING
        mock_task.apply.assert_called_once()
        assert alert_count >= 1


class TestSeedRecommendations:
    def test_creates_recommendations_with_evidence(self, tenant):
        from core.management.commands.seed_real_data import _seed_recommendations

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        _make_classified_items(tenant, source, 15)

        items_qs = FeedbackItem.objects.filter(tenant=tenant).order_by("-received_at")
        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        recs = _seed_recommendations(tenant, items_qs, period_start, period_end)

        assert len(recs) == 3
        for rec in recs:
            assert rec.tenant == tenant
            assert rec.status == Recommendation.Status.PROPOSED
            assert RecommendationEvidence.objects.filter(recommendation=rec).exists()

    def test_idempotent_on_rerun(self, tenant):
        from core.management.commands.seed_real_data import _seed_recommendations

        source = Source.objects.create(
            tenant=tenant, name="Test Source 2", source_type=Source.SourceType.API_PULL, config={}
        )
        _make_classified_items(tenant, source, 15)

        items_qs = FeedbackItem.objects.filter(tenant=tenant).order_by("-received_at")
        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        _seed_recommendations(tenant, items_qs, period_start, period_end)
        _seed_recommendations(tenant, items_qs, period_start, period_end)

        assert Recommendation.objects.filter(tenant=tenant).count() == 3


class TestResetData:
    def test_reset_deletes_all_data(self, tenant):
        from core.management.commands.seed_real_data import _reset_data

        from analysis.models import Correction, CorrectionDisagreement, GoldSetItem, PromptVersion, Recommendation, RecommendationEvidence, RecommendationOutcome
        from reports.models import Report, ReportSection
        from themes.models import Theme
        from trends.models import Alert, TrendSnapshot

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        items = _make_classified_items(tenant, source, 5)
        Correction.objects.create(
            feedback_item=items[0], tenant=tenant,
            field_corrected="sentiment", ai_value="neutral", human_value="negative",
        )
        CorrectionDisagreement.objects.create(
            tenant=tenant, feedback_item=items[0], field_corrected="sentiment",
            correction_ids=[str(items[0].id)], resolution_status="pending",
        )
        GoldSetItem.objects.create(
            tenant=tenant, feedback_item=items[0],
            gold_sentiment="negative", gold_urgency="high", gold_themes=["bug"],
        )
        PromptVersion.objects.create(
            tenant=tenant, version=1, prompt_template="test", active=True,
        )
        rec = Recommendation.objects.create(
            tenant=tenant, title="Test rec", problem_statement="p",
            proposed_action="a", impact_score=0.7, effort_score=0.4,
            confidence=0.7, priority_score=0.7, status=Recommendation.Status.PROPOSED,
        )
        RecommendationEvidence.objects.create(
            tenant=tenant, recommendation=rec, feedback_item=items[0],
        )
        RecommendationOutcome.objects.create(
            tenant=tenant, recommendation=rec, measured_at=date(2026, 4, 15),
            metric_name="accuracy", baseline_value=0.8, current_value=0.85, delta=0.05,
        )
        ReportSection.objects.create(
            tenant=tenant, report=Report.objects.create(
                tenant=tenant, report_type="weekly_outlook",
                period_start=date(2026, 4, 13), period_end=date(2026, 4, 19),
                status=Report.Status.READY,
            ),
            section_type="exec_summary", order=0, raw_content={},
        )
        Alert.objects.create(
            tenant=tenant, alert_type=Alert.AlertType.VOLUME_SPIKE,
            severity=Alert.Severity.WARNING, title="t", description="d",
        )
        TrendSnapshot.objects.create(
            tenant=tenant, snapshot_date=date(2026, 4, 15), metrics={"total_accuracy": 0.8},
        )
        Theme.objects.create(tenant=tenant, slug="test-theme", name="Test Theme", description="d")

        assert FeedbackItem.objects.filter(tenant=tenant).count() > 0
        assert Source.objects.filter(tenant=tenant).count() > 0
        assert Correction.objects.filter(tenant=tenant).count() > 0
        assert Theme.objects.filter(tenant=tenant).count() > 0

        _reset_data()

        assert FeedbackItem.objects.filter(tenant=tenant).count() == 0
        assert Source.objects.filter(tenant=tenant).count() == 0
        assert Correction.objects.filter(tenant=tenant).count() == 0
        assert CorrectionDisagreement.objects.filter(tenant=tenant).count() == 0
        assert GoldSetItem.objects.filter(tenant=tenant).count() == 0
        assert PromptVersion.objects.filter(tenant=tenant).count() == 0
        assert Recommendation.objects.filter(tenant=tenant).count() == 0
        assert RecommendationEvidence.objects.filter(tenant=tenant).count() == 0
        assert RecommendationOutcome.objects.filter(tenant=tenant).count() == 0
        assert Report.objects.filter(tenant=tenant).count() == 0
        assert ReportSection.objects.filter(tenant=tenant).count() == 0
        assert Alert.objects.filter(tenant=tenant).count() == 0
        assert TrendSnapshot.objects.filter(tenant=tenant).count() == 0
        assert Theme.objects.filter(tenant=tenant).count() == 0
        assert Tenant.objects.filter(id=tenant.id).exists()


class TestDryRun:
    @patch("core.management.commands.seed_real_data._run_pipeline_sync")
    @patch("core.management.commands.seed_real_data._scrape_reviews")
    def test_dry_run_does_not_write_to_db(self, mock_scrape, mock_pipeline, tenant):
        from io import StringIO

        mock_scrape.return_value = [
            {"reviewId": "gp:1", "content": "Ok", "userName": "X", "at": "2026-04-10T10:00:00Z", "score": 3},
        ]

        out = StringIO()
        call_command("seed_real_data", tenant_id=str(tenant.id), dry_run=True, stdout=out)

        assert FeedbackItem.objects.filter(tenant=tenant).count() == 0
        assert Source.objects.filter(tenant=tenant).count() == 0


class TestIdempotentRerun:
    def test_second_run_no_duplicate_items(self, tenant):
        from core.management.commands.seed_real_data import _create_source_and_items

        reviews = [
            {"reviewId": "gp:1", "content": "First", "userName": "U1", "at": "2026-04-10T10:00:00Z", "score": 5},
            {"reviewId": "gp:2", "content": "Second", "userName": "U2", "at": "2026-04-11T10:00:00Z", "score": 3},
        ]

        _, count1 = _create_source_and_items(tenant, reviews, "Source A")
        _, count2 = _create_source_and_items(tenant, reviews, "Source A")

        assert count1 == 2
        assert count2 == 0
        assert FeedbackItem.objects.filter(tenant=tenant).count() == 2

    def test_second_run_no_duplicate_reports(self, tenant):
        from core.management.commands.seed_real_data import _seed_report_and_alerts

        period_start = date(2026, 4, 13)
        period_end = date(2026, 4, 19)

        with patch("core.management.commands.seed_real_data.generate_report_task") as mock_task:
            mock_task.apply = MagicMock()
            with patch("django.test.override_settings"):
                report1, _ = _seed_report_and_alerts(tenant, period_start, period_end)
                report2, _ = _seed_report_and_alerts(tenant, period_start, period_end)

        assert Report.objects.filter(tenant=tenant).count() == 1
        assert report1.id == report2.id


class TestSeedOutcomes:
    def test_accepts_rec_and_measures_outcome(self, tenant):
        from core.management.commands.seed_real_data import _seed_outcomes

        source = Source.objects.create(
            tenant=tenant, name="Test Source", source_type=Source.SourceType.API_PULL, config={}
        )
        _make_classified_items(tenant, source, 15)

        items_qs = FeedbackItem.objects.filter(tenant=tenant).order_by("-received_at")

        recs = []
        for i in range(2):
            rec = Recommendation.objects.create(
                tenant=tenant,
                title=f"Test rec {i}",
                problem_statement="problem",
                proposed_action="action",
                impact_score=0.7,
                effort_score=0.4,
                confidence=0.7,
                priority_score=0.7,
                status=Recommendation.Status.PROPOSED,
            )
            item = items_qs[i]
            RecommendationEvidence.objects.create(
                tenant=tenant,
                recommendation=rec,
                feedback_item=item,
            )
            recs.append(rec)

        outcome_count = _seed_outcomes(tenant, recs)

        recs[0].refresh_from_db()
        assert recs[0].status == Recommendation.Status.ACCEPTED
        assert recs[0].decided_at is not None
        assert outcome_count >= 1