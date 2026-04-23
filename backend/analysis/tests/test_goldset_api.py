import pytest
from django.utils import timezone

from core.models import Tenant
from ingestion.models import Source, FeedbackItem
from analysis.models import GoldSetItem


@pytest.mark.django_db
def test_list_gold_set_items(tenant, source, api_client):
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
    )

    r = api_client.get("/api/analysis/gold-set/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["gold_sentiment"] == "positive"
    assert data[0]["gold_themes"] == ["billing"]


@pytest.mark.django_db
def test_create_gold_set_item(tenant, source, api_client):
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )

    r = api_client.post("/api/analysis/gold-set/", {
        "feedback_item": str(item.id),
        "gold_sentiment": "positive",
        "gold_urgency": "low",
        "gold_themes": ["billing"],
    }, format="json")
    assert r.status_code == 201
    data = r.json()
    assert data["gold_sentiment"] == "positive"
    assert GoldSetItem.objects.filter(tenant=tenant).count() == 1


@pytest.mark.django_db
def test_create_gold_set_item_rejects_wrong_tenant_feedback_item(tenant, source, api_client):
    other = Tenant.objects.create(name="Other")
    other_source = Source.objects.create(tenant=other, name="Other", source_type="webhook")
    other_item = FeedbackItem.objects.create(
        tenant=other, source=other_source, content="other",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )

    r = api_client.post("/api/analysis/gold-set/", {
        "feedback_item": str(other_item.id),
        "gold_sentiment": "positive",
        "gold_urgency": "low",
        "gold_themes": ["billing"],
    }, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_delete_gold_set_item(tenant, source, api_client):
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )
    gold = GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
    )

    r = api_client.delete(f"/api/analysis/gold-set/{gold.id}/")
    assert r.status_code == 204
    assert GoldSetItem.objects.filter(id=gold.id).count() == 0


@pytest.mark.django_db
def test_gold_set_list_tenant_scoped(tenant, source, api_client):
    other = Tenant.objects.create(name="Other")
    other_source = Source.objects.create(tenant=other, name="Other", source_type="webhook")
    other_item = FeedbackItem.objects.create(
        tenant=other, source=other_source, content="other",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )
    GoldSetItem.objects.create(
        tenant=other, feedback_item=other_item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
    )

    r = api_client.get("/api/analysis/gold-set/")
    assert r.status_code == 200
    assert len(r.json()) == 0


@pytest.mark.django_db
def test_gold_eval_api_endpoint(tenant, source, api_client):
    from analysis.models import GoldSetItem
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now(),
    )
    GoldSetItem.objects.create(
        tenant=tenant, feedback_item=item,
        gold_sentiment="positive", gold_urgency="low", gold_themes=["billing"],
    )

    r = api_client.get("/api/analysis/eval/gold/")
    assert r.status_code == 200
    data = r.json()
    assert data["items_evaluated"] == 1
    assert data["overall_accuracy"] == 1.0