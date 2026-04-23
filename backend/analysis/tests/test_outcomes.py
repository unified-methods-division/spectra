import pytest
from datetime import date, timedelta
from django.utils import timezone


@pytest.mark.django_db
def test_measure_outcome_for_accepted_recommendation(tenant, source):
    from analysis.outcomes import measure_recommendation_outcome
    from analysis.models import Recommendation, RecommendationEvidence, RecommendationOutcome
    from ingestion.models import FeedbackItem

    rec = Recommendation.objects.create(
        tenant=tenant, title="Test", problem_statement="x",
        proposed_action="x", impact_score=0.8, effort_score=0.3,
        confidence=0.7, priority_score=0.75,
        status=Recommendation.Status.ACCEPTED,
    )
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="negative feedback",
        received_at=timezone.now() - timedelta(days=20),
        sentiment="negative", urgency="high", themes=["billing"],
        processed_at=timezone.now(),
    )
    RecommendationEvidence.objects.create(
        tenant=tenant, recommendation=rec, feedback_item=item,
        evidence_weight=1.0,
    )

    outcomes = measure_recommendation_outcome(str(rec.id))
    assert len(outcomes) > 0
    for o in outcomes:
        assert o.baseline_value is not None
        assert o.delta is not None


@pytest.mark.django_db
def test_measure_outcome_only_for_accepted(tenant, source):
    from analysis.outcomes import measure_recommendation_outcome
    from analysis.models import Recommendation

    rec = Recommendation.objects.create(
        tenant=tenant, title="Test", problem_statement="x",
        proposed_action="x", impact_score=0.8, effort_score=0.3,
        confidence=0.7, priority_score=0.75,
        status=Recommendation.Status.PROPOSED,
    )
    outcomes = measure_recommendation_outcome(str(rec.id))
    assert len(outcomes) == 0


@pytest.mark.django_db
def test_drift_delta_computed_from_snapshots(tenant, source):
    from analysis.outcomes import compute_drift_delta
    from trends.models import TrendSnapshot

    today = date.today()
    for i in range(14):
        TrendSnapshot.objects.create(
            tenant=tenant,
            snapshot_date=today - timedelta(days=13 - i),
            metrics={"total_accuracy": 0.80 + i * 0.01},
        )

    entries = compute_drift_delta(str(tenant.id), weeks=2)
    assert len(entries) >= 1
    if len(entries) >= 2:
        last = entries[-1]
        assert last.accuracy > entries[0].accuracy


@pytest.mark.django_db
def test_drift_delta_empty_when_no_snapshots(tenant, source):
    from analysis.outcomes import compute_drift_delta
    entries = compute_drift_delta(str(tenant.id), weeks=4)
    assert len(entries) == 0


@pytest.mark.django_db
def test_outcome_api_endpoint(tenant, source, api_client):
    from analysis.models import Recommendation, RecommendationEvidence
    from ingestion.models import FeedbackItem

    rec = Recommendation.objects.create(
        tenant=tenant, title="Test", problem_statement="x",
        proposed_action="x", impact_score=0.8, effort_score=0.3,
        confidence=0.7, priority_score=0.75,
        status=Recommendation.Status.ACCEPTED,
    )
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="test",
        received_at=timezone.now() - timedelta(days=20),
        sentiment="negative", urgency="high", themes=["billing"],
        processed_at=timezone.now(),
    )
    RecommendationEvidence.objects.create(
        tenant=tenant, recommendation=rec, feedback_item=item,
    )

    r = api_client.get(f"/api/analysis/recommendations/{rec.id}/outcome/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.django_db
def test_drift_api_endpoint(tenant, source, api_client):
    from trends.models import TrendSnapshot

    today = date.today()
    for i in range(7):
        TrendSnapshot.objects.create(
            tenant=tenant,
            snapshot_date=today - timedelta(days=6 - i),
            metrics={"total_accuracy": 0.85},
        )

    r = api_client.get("/api/analysis/eval/drift/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.django_db
def test_measure_outcome_idempotent(tenant, source):
    from analysis.outcomes import measure_recommendation_outcome
    from analysis.models import Recommendation, RecommendationEvidence, RecommendationOutcome
    from ingestion.models import FeedbackItem

    rec = Recommendation.objects.create(
        tenant=tenant, title="Test", problem_statement="x",
        proposed_action="x", impact_score=0.8, effort_score=0.3,
        confidence=0.7, priority_score=0.75,
        status=Recommendation.Status.ACCEPTED,
    )
    item = FeedbackItem.objects.create(
        tenant=tenant, source=source, content="negative feedback",
        received_at=timezone.now() - timedelta(days=20),
        sentiment="negative", urgency="high", themes=["billing"],
        processed_at=timezone.now(),
    )
    RecommendationEvidence.objects.create(
        tenant=tenant, recommendation=rec, feedback_item=item,
        evidence_weight=1.0,
    )

    first = measure_recommendation_outcome(str(rec.id))
    second = measure_recommendation_outcome(str(rec.id))
    assert len(first) == len(second)
    assert RecommendationOutcome.objects.filter(recommendation=rec).count() == len(first)