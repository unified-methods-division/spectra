import pytest
from analysis.models import GoldSetItem, Correction, PromptVersion
from analysis.eval import run_gold_eval, EvalResult
from ingestion.models import FeedbackItem, Source


@pytest.fixture
def gold_source(tenant):
    return Source.objects.create(
        tenant=tenant, name="Gold Source", source_type=Source.SourceType.WEBHOOK
    )


@pytest.fixture
def gold_items(tenant, gold_source):
    items = []
    for i in range(5):
        item = FeedbackItem.objects.create(
            tenant=tenant,
            source=gold_source,
            content=f"Gold feedback {i}",
            received_at="2026-01-01T00:00:00Z",
            sentiment="negative",
            urgency="high",
            themes=["billing", "performance"],
            processed_at="2026-01-01T00:00:00Z",
        )
        items.append(item)
    return items


@pytest.mark.django_db
def test_run_gold_eval_empty_gold_set(tenant):
    result = run_gold_eval(str(tenant.id))
    assert result.field_accuracy == {}
    assert result.theme_precision == 0.0
    assert result.theme_recall == 0.0
    assert result.overall_accuracy == 0.0
    assert result.items_evaluated == 0


@pytest.mark.django_db
def test_run_gold_eval_full_agreement(tenant, gold_items):
    for item in gold_items:
        GoldSetItem.objects.create(
            tenant=tenant,
            feedback_item=item,
            gold_sentiment="negative",
            gold_urgency="high",
            gold_themes=["billing", "performance"],
        )

    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 5
    assert result.field_accuracy["sentiment"] == 1.0
    assert result.field_accuracy["urgency"] == 1.0
    assert result.theme_precision == 1.0
    assert result.theme_recall == 1.0
    assert result.overall_accuracy == 1.0


@pytest.mark.django_db
def test_run_gold_eval_partial_disagreement(tenant, gold_items):
    GoldSetItem.objects.create(
        tenant=tenant,
        feedback_item=gold_items[0],
        gold_sentiment="positive",
        gold_urgency="high",
        gold_themes=["billing", "performance"],
    )
    GoldSetItem.objects.create(
        tenant=tenant,
        feedback_item=gold_items[1],
        gold_sentiment="negative",
        gold_urgency="low",
        gold_themes=["billing"],
    )

    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 2
    assert result.field_accuracy["sentiment"] == 0.5
    assert result.field_accuracy["urgency"] == 0.5


@pytest.mark.django_db
def test_run_gold_eval_theme_precision_recall(tenant, gold_items):
    gold_items[0].themes = ["billing", "performance", "usability"]
    gold_items[0].save()

    GoldSetItem.objects.create(
        tenant=tenant,
        feedback_item=gold_items[0],
        gold_sentiment="negative",
        gold_urgency="high",
        gold_themes=["billing", "performance"],
    )

    result = run_gold_eval(str(tenant.id))
    assert result.items_evaluated == 1
    assert result.theme_precision == 1.0
    assert result.theme_recall == 1.0

    gold_items[0].themes = ["billing"]
    gold_items[0].save()

    result = run_gold_eval(str(tenant.id))
    assert result.theme_precision == 1.0
    assert result.theme_recall == 0.5


@pytest.mark.django_db
def test_run_gold_eval_field_level_breakdown(tenant, gold_items):
    for i, item in enumerate(gold_items):
        GoldSetItem.objects.create(
            tenant=tenant,
            feedback_item=item,
            gold_sentiment="positive",
            gold_urgency="low" if i < 3 else "high",
            gold_themes=["billing", "performance"],
        )

    result = run_gold_eval(str(tenant.id))
    assert result.field_accuracy["sentiment"] == 0.0
    assert result.field_accuracy["urgency"] == pytest.approx(0.4, abs=0.01)


@pytest.mark.django_db
def test_run_gold_eval_with_prompt_version(tenant, gold_items):
    for item in gold_items:
        GoldSetItem.objects.create(
            tenant=tenant,
            feedback_item=item,
            gold_sentiment="negative",
            gold_urgency="high",
            gold_themes=["billing", "performance"],
        )

    pv = PromptVersion.objects.create(
        tenant=tenant,
        version=1,
        prompt_template="test",
        active=True,
    )

    for item in gold_items[:3]:
        Correction.objects.create(
            tenant=tenant,
            feedback_item=item,
            field_corrected="sentiment",
            ai_value="positive",
            human_value="negative",
        )

    result = run_gold_eval(str(tenant.id), prompt_version_id=str(pv.id))
    assert result.items_evaluated == 5
    assert result.field_accuracy["sentiment"] == 1.0