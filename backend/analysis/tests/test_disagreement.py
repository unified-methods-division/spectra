import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_two_corrections_different_human_values_creates_disagreement(tenant, source):
    from analysis.disagreement import detect_disagreements_for_item_field
    from analysis.models import Correction, CorrectionDisagreement
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )

    result = detect_disagreements_for_item_field(str(tenant.id), str(item.id), "sentiment")
    assert result is not None
    assert result.resolution_status == "pending"
    assert len(result.correction_ids) == 2


@pytest.mark.django_db
def test_two_corrections_same_human_value_no_disagreement(tenant, source):
    from analysis.disagreement import detect_disagreements_for_item_field
    from analysis.models import Correction, CorrectionDisagreement
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )

    result = detect_disagreements_for_item_field(str(tenant.id), str(item.id), "sentiment")
    assert result is None


@pytest.mark.django_db
def test_resolve_disagreement_sets_resolved_value(tenant, source):
    from analysis.disagreement import detect_disagreements_for_item_field, resolve_disagreement
    from analysis.models import Correction, CorrectionDisagreement
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )

    disagreement = detect_disagreements_for_item_field(str(tenant.id), str(item.id), "sentiment")
    assert disagreement is not None

    resolved = resolve_disagreement(str(disagreement.id), "negative")
    assert resolved.resolution_status == "resolved"
    assert resolved.resolved_value == "negative"
    assert resolved.resolved_at is not None

    item.refresh_from_db()
    assert item.sentiment == "negative"


@pytest.mark.django_db
def test_disagreement_rate_computed_correctly(tenant, source):
    from analysis.disagreement import disagreement_rate, detect_disagreements
    from analysis.models import Correction
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="urgency", ai_value="low", human_value="high"
    )

    detect_disagreements(str(tenant.id))
    rate = disagreement_rate(str(tenant.id))
    assert abs(rate - 33.33) < 1


@pytest.mark.django_db
def test_disagreement_list_api(tenant, source, api_client):
    from analysis.disagreement import detect_disagreements
    from analysis.models import Correction
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )
    detect_disagreements(str(tenant.id))

    r = api_client.get("/api/analysis/disagreements/")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.django_db
def test_disagreement_resolve_api(tenant, source, api_client):
    from analysis.disagreement import detect_disagreements
    from analysis.models import Correction, CorrectionDisagreement
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )
    detect_disagreements(str(tenant.id))

    disagreement = CorrectionDisagreement.objects.filter(tenant=tenant).first()

    r = api_client.post(
        f"/api/analysis/disagreements/{disagreement.id}/resolve/",
        {"resolved_value": "negative"},
        format="json",
    )
    assert r.status_code == 200
    assert r.json()["resolution_status"] == "resolved"
    assert r.json()["resolved_value"] == "negative"


@pytest.mark.django_db
def test_disagreement_rate_api(tenant, source, api_client):
    from analysis.disagreement import detect_disagreements
    from analysis.models import Correction
    from ingestion.models import FeedbackItem

    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=tenant, feedback_item=item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )
    detect_disagreements(str(tenant.id))

    r = api_client.get("/api/analysis/disagreements/rate/")
    assert r.status_code == 200
    assert "disagreement_rate" in r.json()


@pytest.mark.django_db
def test_disagreement_tenant_scoping(tenant, source, api_client):
    from analysis.disagreement import detect_disagreements
    from analysis.models import Correction, CorrectionDisagreement
    from core.models import Tenant
    from ingestion.models import Source, FeedbackItem

    other = Tenant.objects.create(name="Other")
    other_source = Source.objects.create(tenant=other, name="Other", source_type="webhook")
    other_item = FeedbackItem.objects.create(
        tenant=other, source=other_source, content="other",
        received_at=timezone.now(), sentiment="positive",
        urgency="low", themes=["billing"],
        processed_at=timezone.now()
    )
    Correction.objects.create(
        tenant=other, feedback_item=other_item,
        field_corrected="sentiment", ai_value="positive", human_value="negative"
    )
    Correction.objects.create(
        tenant=other, feedback_item=other_item,
        field_corrected="sentiment", ai_value="positive", human_value="neutral"
    )
    detect_disagreements(str(other.id))

    r = api_client.get("/api/analysis/disagreements/")
    assert r.status_code == 200
    assert len(r.json()) == 0