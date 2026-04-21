"""
Tests for polish service guardrails.

Invariants covered:
- INV-002: LLM polish layer cannot invent facts (P0)
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestPolishGuardrails:
    """INV-002: LLM polish cannot invent facts."""

    @pytest.mark.asyncio
    async def test_polish_cannot_add_facts(self, raw_report_data):
        """Extract facts from raw and polished; polished ⊆ raw."""
        from reports.services.polish import PolishService

        service = PolishService()

        # Mock LLM to return polished content with an invented number
        mock_polished = type(
            "MockPolished",
            (),
            {
                "title": "Executive Summary",
                "body": "This week we received 999 feedback items with 50% positive sentiment.",
                "key_points": ["999 items received", "50% positive"],
            },
        )()

        with patch.object(service.agent, "run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = type("MockResult", (), {"output": mock_polished})()

            polished, used_fallback = await service.polish_section(
                raw_content=raw_report_data["this_week"],
                section_type="exec_summary",
            )

            # If validation fails (invented 999), should fallback
            # raw_report_data has total_items=247, not 999
            assert used_fallback is True or polished is None, (
                "Invented facts must be rejected"
            )

    @pytest.mark.asyncio
    async def test_polish_timeout_fallback(self, mocker, raw_report_data):
        """EM-002-D: LLM timeout → fallback to raw."""
        from reports.services.polish import PolishService, create_fallback_polished
        import asyncio

        service = PolishService()

        with patch.object(service.agent, "run", side_effect=asyncio.TimeoutError):
            polished, used_fallback = await service.polish_section(
                raw_content=raw_report_data["this_week"],
                section_type="exec_summary",
            )

            assert used_fallback is True
            assert polished is None

    def test_fallback_produces_valid_output(self, raw_report_data):
        """Fallback formatters produce valid structured output."""
        from reports.services.polish import create_fallback_polished

        section_types = [
            "exec_summary",
            "whats_changed",
            "whats_working",
            "needs_attention",
            "recommendations",
            "decisions_made",
        ]

        for section_type in section_types:
            content = raw_report_data.get(section_type, {})
            fallback = create_fallback_polished(content, section_type)

            assert "title" in fallback
            assert "body" in fallback
            assert "key_points" in fallback
            assert isinstance(fallback["key_points"], list)
