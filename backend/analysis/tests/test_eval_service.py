import pytest
from django.utils import timezone

from core.models import Tenant
from ingestion.models import Source, FeedbackItem
from analysis.models import GoldSetItem, Correction


@pytest.mark.django_db
def test_empty_gold_set_returns_zeroes(tenant, source):
    from analysis.eval import run_gold_eval

    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 0
    assert result.overall_accuracy == 0.0
    assert result.theme_precision == 0.0
    assert result.theme_recall == 0.0


@pytest.mark.django_db
def test_full_agreement_returns_perfect_accuracy(tenant, source):
    from analysis.eval import run_gold_eval

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"]
    )
    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 1
    assert result.overall_accuracy == 1.0


@pytest.mark.django_db
def test_partial_disagreement_field_accuracy(tenant, source):
    from analysis.eval import run_gold_eval

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="high", themes=["billing"],
        processed_at=timezone.now()
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"]
    )
    result = run_gold_eval(str(tenant.id))
    assert result.field_accuracy["sentiment"] == 1.0
    assert result.field_accuracy["urgency"] == 0.0


@pytest.mark.django_db
def test_theme_precision_and_recall(tenant, source):
    from analysis.eval import run_gold_eval

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing", "performance"],
        processed_at=timezone.now()
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing", "usability"]
    )
    result = run_gold_eval(str(tenant.id))
    # AI predicted {billing, performance}, gold is {billing, usability}
    # Intersection: {billing}, AI union: {billing, performance}, Gold union: {billing, usability}
    # Precision = |intersection| / |AI predicted| = 1/2 = 0.5
    # Recall = |intersection| / |Gold| = 1/2 = 0.5
    assert result.theme_precision == 0.5
    assert result.theme_recall == 0.5


@pytest.mark.django_db
def test_uses_correction_ai_value_not_current_field(tenant, source):
    from analysis.eval import run_gold_eval

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="negative",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"]
    )
    result = run_gold_eval(str(tenant.id))
    assert result.field_accuracy["sentiment"] == 1.0


@pytest.mark.django_db
def test_tenant_scoping(tenant, source, db):
    from analysis.eval import run_gold_eval

    other_tenant = Tenant.objects.create(name="Other")
    other_source = Source.objects.create(tenant=other_tenant, name="Other Source", source_type="webhook")

    item_other = FeedbackItem.objects.create(
        tenant=other_tenant, source=other_source, content="other",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    GoldSetItem.objects.create(
        tenant=other_tenant, feedback_item=item_other,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"]
    )
    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 0