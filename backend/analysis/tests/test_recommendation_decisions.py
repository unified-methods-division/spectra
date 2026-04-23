import pytest


@pytest.mark.django_db
def test_recommendation_decision_updates_status_owner_and_decided_at(tenant, api_client):
    from analysis.models import Recommendation

    rec = Recommendation.objects.create(
        tenant=tenant,
        title="Fix billing bug",
        problem_statement="Billing complaints rising",
        proposed_action="Audit billing calculation",
        impact_score=0.8,
        effort_score=0.3,
        confidence=0.7,
        priority_score=0.76,
        status=Recommendation.Status.PROPOSED,
    )

    r = api_client.post(
        f"/api/analysis/recommendations/{rec.id}/decide/",
        {"status": "accepted", "decision_owner": "alex"},
        format="json",
    )

    assert r.status_code == 200
    payload = r.json()
    assert payload["status"] == "accepted"
    assert payload["decision_owner"] == "alex"
    assert payload["decided_at"] is not None

    rec.refresh_from_db()
    assert rec.status == "accepted"
    assert rec.decision_owner == "alex"
    assert rec.decided_at is not None


@pytest.mark.django_db
def test_recommendation_decision_rejects_invalid_status(tenant, api_client):
    from analysis.models import Recommendation

    rec = Recommendation.objects.create(
        tenant=tenant,
        title="x",
        problem_statement="x",
        proposed_action="x",
        impact_score=0.5,
        effort_score=0.5,
        confidence=0.5,
        priority_score=0.5,
        status=Recommendation.Status.PROPOSED,
    )

    r = api_client.post(
        f"/api/analysis/recommendations/{rec.id}/decide/",
        {"status": "proposed"},
        format="json",
    )
    assert r.status_code == 400
    rec.refresh_from_db()
    assert rec.status == "proposed"


@pytest.mark.django_db
def test_recommendation_decision_is_tenant_scoped(tenant, api_client):
    from core.models import Tenant
    from analysis.models import Recommendation

    other = Tenant.objects.create(name="Other")
    rec_other = Recommendation.objects.create(
        tenant=other,
        title="x",
        problem_statement="x",
        proposed_action="x",
        impact_score=0.5,
        effort_score=0.5,
        confidence=0.5,
        priority_score=0.5,
        status=Recommendation.Status.PROPOSED,
    )

    r = api_client.post(
        f"/api/analysis/recommendations/{rec_other.id}/decide/",
        {"status": "dismissed"},
        format="json",
    )
    assert r.status_code == 404
    rec_other.refresh_from_db()
    assert rec_other.status == "proposed"

