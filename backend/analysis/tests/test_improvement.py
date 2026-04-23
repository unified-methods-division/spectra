import pytest
from datetime import date, timedelta
from django.utils import timezone

from analysis.models import Correction, GoldSetItem, PromptVersion
from ingestion.models import FeedbackItem

TOMORROW = date.today() + timedelta(days=1)


@pytest.mark.django_db
def test_regression_gate_blocks_promotion_when_gold_accuracy_lower(tenant, source):
    """New prompt version with lower gold-set accuracy than previous → NOT activated."""
    prev = PromptVersion.objects.create(
        tenant=tenant, version=1, prompt_template="v1",
        accuracy_at_creation=0.9, accuracy_current=0.9, active=True,
    )

    for i in range(5):
        item = FeedbackItem.objects.create(
            tenant=tenant, source=source, content=f"gold item {i}",
            received_at=timezone.now() - timezone.timedelta(days=1),
            sentiment="negative", urgency="low", themes=["billing"],
            processed_at=timezone.now(),
        )
        GoldSetItem.objects.create(
            tenant=tenant, feedback_item=item,
            gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
        )

    for i in range(6):
        Correction.objects.create(
            tenant=tenant,
            feedback_item=FeedbackItem.objects.create(
                tenant=tenant, source=source, content=f"corr item {i}",
                received_at=timezone.now() - timezone.timedelta(days=1),
                sentiment="negative", urgency="low", themes=["billing"],
                processed_at=timezone.now(),
            ),
            field_corrected="sentiment",
            ai_value="negative",
            human_value="positive",
        )

    from analysis.improvement import assess_corrections
    result = assess_corrections(str(tenant.id), end_date=TOMORROW)

    assert result is not None
    result.refresh_from_db()
    assert result.active is False
    assert result.regression_note is not None
    assert "gold" in result.regression_note.lower()
    prev.refresh_from_db()
    assert prev.active is True


@pytest.mark.django_db
def test_regression_gate_allows_promotion_when_gold_accuracy_higher(tenant, source):
    """New prompt version with higher gold-set accuracy → activated."""
    prev = PromptVersion.objects.create(
        tenant=tenant, version=1, prompt_template="v1",
        accuracy_at_creation=0.1, accuracy_current=0.1, active=True,
    )

    for i in range(5):
        item = FeedbackItem.objects.create(
            tenant=tenant, source=source, content=f"gold item {i}",
            received_at=timezone.now() - timezone.timedelta(days=1),
            sentiment="positive", urgency="low", themes=["billing"],
            processed_at=timezone.now(),
        )
        GoldSetItem.objects.create(
            tenant=tenant, feedback_item=item,
            gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
        )

    for i in range(6):
        Correction.objects.create(
            tenant=tenant,
            feedback_item=FeedbackItem.objects.create(
                tenant=tenant, source=source, content=f"corr item {i}",
                received_at=timezone.now() - timezone.timedelta(days=1),
                sentiment="positive", urgency="low", themes=["billing"],
                processed_at=timezone.now(),
            ),
            field_corrected="sentiment",
            ai_value="negative",
            human_value="positive",
        )

    from analysis.improvement import assess_corrections
    result = assess_corrections(str(tenant.id), end_date=TOMORROW)

    assert result is not None
    result.refresh_from_db()
    assert result.active is True
    assert result.regression_note is None


@pytest.mark.django_db
def test_fallback_to_float_comparison_when_no_gold_set(tenant, source):
    """No gold set exists → falls back to current float comparison logic."""
    prev = PromptVersion.objects.create(
        tenant=tenant, version=1, prompt_template="v1",
        accuracy_at_creation=0.1, accuracy_current=0.1, active=True,
    )

    for i in range(6):
        Correction.objects.create(
            tenant=tenant,
            feedback_item=FeedbackItem.objects.create(
                tenant=tenant, source=source, content=f"corr item {i}",
                received_at=timezone.now() - timezone.timedelta(days=1),
                sentiment="negative", urgency="low", themes=["billing"],
                processed_at=timezone.now(),
            ),
            field_corrected="sentiment",
            ai_value="negative",
            human_value="positive",
        )

    from analysis.improvement import assess_corrections
    result = assess_corrections(str(tenant.id), end_date=TOMORROW)

    assert result is not None
    result.refresh_from_db()
    assert result.regression_note is None


@pytest.mark.django_db
def test_regression_gate_no_previous_version_promotes(tenant, source):
    """No previous version → promote regardless of gold eval (first version)."""
    for i in range(5):
        item = FeedbackItem.objects.create(
            tenant=tenant, source=source, content=f"gold item {i}",
            received_at=timezone.now() - timezone.timedelta(days=1),
            sentiment="negative", urgency="low", themes=["billing"],
            processed_at=timezone.now(),
        )
        GoldSetItem.objects.create(
            tenant=tenant, feedback_item=item,
            gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
        )

    for i in range(6):
        Correction.objects.create(
            tenant=tenant,
            feedback_item=FeedbackItem.objects.create(
                tenant=tenant, source=source, content=f"corr item {i}",
                received_at=timezone.now() - timezone.timedelta(days=1),
                sentiment="negative", urgency="low", themes=["billing"],
                processed_at=timezone.now(),
            ),
            field_corrected="sentiment",
            ai_value="negative",
            human_value="positive",
        )

    from analysis.improvement import assess_corrections
    result = assess_corrections(str(tenant.id), end_date=TOMORROW)

    assert result is not None
    result.refresh_from_db()
    assert result.active is True
    assert result.regression_note is None


@pytest.mark.django_db
def test_regression_gate_stores_accuracy_from_gold_eval(tenant, source):
    """When gold set exists and promotion succeeds, accuracy_at_creation reflects gold eval."""
    prev = PromptVersion.objects.create(
        tenant=tenant, version=1, prompt_template="v1",
        accuracy_at_creation=0.1, accuracy_current=0.1, active=True,
    )

    for i in range(5):
        item = FeedbackItem.objects.create(
            tenant=tenant, source=source, content=f"gold item {i}",
            received_at=timezone.now() - timezone.timedelta(days=1),
            sentiment="positive", urgency="low", themes=["billing"],
            processed_at=timezone.now(),
        )
        GoldSetItem.objects.create(
            tenant=tenant, feedback_item=item,
            gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
        )

    for i in range(6):
        Correction.objects.create(
            tenant=tenant,
            feedback_item=FeedbackItem.objects.create(
                tenant=tenant, source=source, content=f"corr item {i}",
                received_at=timezone.now() - timezone.timedelta(days=1),
                sentiment="positive", urgency="low", themes=["billing"],
                processed_at=timezone.now(),
            ),
            field_corrected="sentiment",
            ai_value="negative",
            human_value="positive",
        )

    from analysis.eval import run_gold_eval
    from analysis.improvement import assess_corrections
    result = assess_corrections(str(tenant.id), end_date=TOMORROW)

    assert result is not None
    expected_accuracy = run_gold_eval(str(tenant.id)).overall_accuracy
    assert result.accuracy_at_creation == expected_accuracy