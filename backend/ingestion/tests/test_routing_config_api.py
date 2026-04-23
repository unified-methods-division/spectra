import pytest


@pytest.mark.django_db
def test_routing_config_put_validates_bounds_and_returns_preview(
    tenant, api_client, source, feedback_items
):
    # Ensure some items are below a strict threshold
    r = api_client.put(
        f"/api/ingestion/sources/{source.id}/routing-config/",
        {"confidence_threshold": 0.95},
        format="json",
    )

    assert r.status_code == 200
    data = r.json()
    assert data["confidence_threshold"] == 0.95
    assert isinstance(data["flagged_preview_count"], int)
    assert data["flagged_preview_count"] >= 0


@pytest.mark.django_db
def test_routing_config_put_rejects_invalid_threshold(tenant, api_client, source):
    r = api_client.put(
        f"/api/ingestion/sources/{source.id}/routing-config/",
        {"confidence_threshold": 1.5},
        format="json",
    )
    assert r.status_code == 400

