"""
Tests for evidence selection service.

Invariants covered:
- INV-004: Evidence selection is traceable (P1)
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone


class TestEvidenceSelection:
    """INV-004: Evidence selection is traceable."""

    @pytest.mark.django_db
    def test_evidence_has_selection_reason(self, recommendation_with_candidates):
        """All report-generated evidence has non-null selection_reason."""
        from reports.services.evidence import select_evidence

        recommendation, candidate_items = recommendation_with_candidates

        evidence_list = select_evidence(recommendation, candidate_items)

        for evidence in evidence_list:
            assert evidence.selection_reason is not None, (
                "Evidence created by service must have selection_reason"
            )
            assert evidence.selection_reason != "", "selection_reason must not be empty"

    @pytest.mark.django_db
    def test_evidence_no_duplicates(self, recommendation_with_candidates):
        """EM-004-C: No duplicate evidence links."""
        from reports.services.evidence import (
            select_evidence,
            link_evidence_for_recommendations,
        )
        from analysis.models import RecommendationEvidence

        recommendation, candidate_items = recommendation_with_candidates

        # Call twice
        evidence1 = select_evidence(recommendation, candidate_items)
        evidence2 = select_evidence(recommendation, candidate_items)

        # Check no duplicates by feedback_item
        item_ids_1 = {e.feedback_item_id for e in evidence1}
        assert len(item_ids_1) == len(evidence1), "Evidence list has duplicates"

    @pytest.mark.django_db
    def test_evidence_max_items_respected(self, recommendation_with_candidates):
        """Evidence selection respects max_items constraint."""
        from reports.services.evidence import select_evidence, SelectionCriteria

        recommendation, candidate_items = recommendation_with_candidates

        criteria = SelectionCriteria(max_items=3)
        evidence_list = select_evidence(recommendation, candidate_items, criteria)

        assert len(evidence_list) <= 3

    @pytest.mark.django_db
    def test_evidence_selection_deterministic(self, recommendation_with_candidates):
        """Same inputs produce same evidence selection."""
        from reports.services.evidence import select_evidence

        recommendation, candidate_items = recommendation_with_candidates

        evidence1 = select_evidence(recommendation, candidate_items)
        evidence2 = select_evidence(recommendation, candidate_items)

        items1 = [e.feedback_item_id for e in evidence1]
        items2 = [e.feedback_item_id for e in evidence2]

        assert items1 == items2, "Evidence selection must be deterministic"
