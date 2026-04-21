"""
Shared pytest fixtures for backend tests.
"""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Tenant
from ingestion.models import Source, FeedbackItem
from analysis.models import Recommendation, RecommendationEvidence


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    return Tenant.objects.create(name="Test Tenant")


@pytest.fixture
def api_client(tenant):
    """Create an API client with tenant header."""
    from django.contrib.auth.models import User
    
    client = APIClient()
    user = User.objects.create_user(username="testuser", password="testpass")
    client.force_authenticate(user=user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.id)
    return client


@pytest.fixture
def source(tenant):
    """Create a test source."""
    return Source.objects.create(
        tenant=tenant,
        name="Test Source",
        source_type=Source.SourceType.WEBHOOK,
    )


@pytest.fixture
def feedback_items(tenant, source):
    """Create sample feedback items for testing."""
    items = []
    base_date = timezone.now() - timedelta(days=7)

    for i in range(20):
        item = FeedbackItem.objects.create(
            tenant=tenant,
            source=source,
            content=f"Test feedback content {i}",
            received_at=base_date + timedelta(hours=i * 2),
            sentiment=["positive", "negative", "neutral"][i % 3],
            sentiment_confidence=0.8 + (i % 3) * 0.05,
            urgency=["low", "medium", "high", "critical"][i % 4],
            themes=["billing", "performance"][:((i % 2) + 1)],
            processed_at=timezone.now(),
        )
        items.append(item)

    return items


@pytest.fixture
def tenant_with_report_data(tenant, source, db):
    """Tenant with feedback items, recommendations, and trend snapshots."""
    from trends.models import TrendSnapshot, Alert

    base_date = timezone.now() - timedelta(days=14)

    # Create 50 feedback items across two weeks
    items = []
    for i in range(50):
        item = FeedbackItem.objects.create(
            tenant=tenant,
            source=source,
            content=f"Feedback item {i} about billing and performance issues",
            received_at=base_date + timedelta(days=i // 4, hours=(i % 4) * 6),
            sentiment=["positive", "negative", "neutral", "mixed"][i % 4],
            sentiment_confidence=0.7 + (i % 3) * 0.1,
            urgency=["low", "medium", "high", "critical"][i % 4],
            themes=["billing", "performance", "usability"][:((i % 3) + 1)],
            processed_at=timezone.now(),
        )
        items.append(item)

    # Create 5 recommendations with evidence
    for i in range(5):
        rec = Recommendation.objects.create(
            tenant=tenant,
            title=f"Recommendation {i}",
            problem_statement=f"Problem statement {i} related to billing",
            proposed_action=f"Proposed action {i}",
            impact_score=0.5 + (i * 0.1),
            effort_score=0.3 + (i * 0.1),
            confidence=0.7 + (i * 0.05),
            priority_score=0.6 + (i * 0.08),
            rationale={"themes": ["billing", "performance"]},
        )

        # Add evidence
        for j in range(3):
            if i * 3 + j < len(items):
                RecommendationEvidence.objects.create(
                    tenant=tenant,
                    recommendation=rec,
                    feedback_item=items[i * 3 + j],
                    evidence_weight=1.0 - (j * 0.1),
                    selection_reason=f"top 3 by urgency + recency | theme match: billing",
                )

    # Create daily trend snapshots
    for i in range(14):
        snapshot_date = (base_date + timedelta(days=i)).date()
        TrendSnapshot.objects.create(
            tenant=tenant,
            snapshot_date=snapshot_date,
            metrics={
                "total_accuracy": 0.85 + (i * 0.005),
                "accuracy_by_theme": {"billing": 0.82, "performance": 0.88},
                "accuracy_by_sentiment": {"positive": 0.9, "negative": 0.8, "neutral": 0.85},
                "accuracy_by_urgency": {"low": 0.9, "medium": 0.85, "high": 0.8, "critical": 0.75},
            },
        )

    # Create a few alerts
    for i in range(3):
        Alert.objects.create(
            tenant=tenant,
            alert_type=["volume_spike", "sentiment_shift", "new_theme"][i % 3],
            severity=["info", "warning", "critical"][i % 3],
            title=f"Alert {i}",
            description=f"Alert description {i}",
        )

    return tenant


@pytest.fixture
def raw_report_data():
    """Sample raw report data for polish testing."""
    return {
        "period_start": "2026-04-13",
        "period_end": "2026-04-19",
        "this_week": {
            "total_items": 247,
            "sentiment_distribution": {"positive": 0.45, "negative": 0.32, "neutral": 0.23},
            "urgency_distribution": {"low": 0.4, "medium": 0.35, "high": 0.2, "critical": 0.05},
            "theme_counts": {"billing": 45, "performance": 38, "usability": 25},
            "accuracy": 0.85,
            "alerts_count": 3,
        },
        "last_week": {
            "total_items": 184,
            "sentiment_distribution": {"positive": 0.42, "negative": 0.35, "neutral": 0.23},
            "urgency_distribution": {"low": 0.45, "medium": 0.3, "high": 0.2, "critical": 0.05},
            "theme_counts": {"billing": 35, "performance": 42, "usability": 20},
            "accuracy": 0.83,
            "alerts_count": 2,
        },
        "delta": {
            "volume_delta": 0.34,
            "sentiment_delta": {"positive": 0.03, "negative": -0.03, "neutral": 0.0},
            "accuracy_delta": 0.02,
            "new_themes": ["onboarding"],
            "rising_themes": ["billing"],
            "declining_themes": ["performance"],
        },
        "exec_summary": {
            "total_items": 247,
            "volume_change": 0.34,
            "accuracy": 0.85,
            "accuracy_change": 0.02,
            "alerts_count": 3,
        },
        "whats_changed": {
            "volume_delta": 0.34,
            "sentiment_delta": {"positive": 0.03, "negative": -0.03},
            "new_themes": ["onboarding"],
            "rising_themes": ["billing"],
            "declining_themes": ["performance"],
        },
        "whats_working": {
            "positive_sentiment_pct": 0.45,
            "improving_themes": ["billing"],
            "accuracy": 0.85,
        },
        "needs_attention": {
            "negative_sentiment_pct": 0.32,
            "attention_items": [
                {"type": "volume_spike", "message": "Volume increased 34%"},
            ],
            "alerts_count": 3,
        },
        "recommendations": {
            "recommendations": [
                {
                    "id": "rec-1",
                    "title": "Improve checkout flow",
                    "priority_score": 0.85,
                },
            ],
            "count": 1,
        },
        "decisions_made": {
            "accepted": 2,
            "dismissed": 1,
            "pending": 1,
            "total": 4,
        },
        "top_recommendations": [
            {
                "id": "rec-1",
                "title": "Improve checkout flow",
                "problem_statement": "Users report checkout issues",
                "proposed_action": "Simplify checkout process",
                "priority_score": 0.85,
                "status": "proposed",
            }
        ],
        "decisions_summary": {
            "accepted": 2,
            "dismissed": 1,
            "needs_more_evidence": 1,
        },
        "generated_at": "2026-04-21T06:00:00Z",
    }


@pytest.fixture
def recommendation_with_candidates(tenant, source):
    """Create a recommendation with candidate feedback items for evidence selection."""
    # Create candidate feedback items
    items = []
    base_date = timezone.now() - timedelta(days=7)

    for i in range(10):
        item = FeedbackItem.objects.create(
            tenant=tenant,
            source=source,
            content=f"Billing issue feedback {i}",
            received_at=base_date + timedelta(hours=i * 12),
            sentiment="negative",
            sentiment_confidence=0.85,
            urgency=["low", "medium", "high", "critical"][i % 4],
            themes=["billing", "checkout"][:((i % 2) + 1)],
            processed_at=timezone.now(),
        )
        items.append(item)

    # Create recommendation
    recommendation = Recommendation.objects.create(
        tenant=tenant,
        title="Fix billing errors",
        problem_statement="Users report billing calculation errors",
        proposed_action="Audit and fix billing calculation logic",
        impact_score=0.8,
        effort_score=0.4,
        confidence=0.85,
        priority_score=0.75,
        rationale={"themes": ["billing", "checkout"]},
    )

    return recommendation, FeedbackItem.objects.filter(tenant=tenant)
