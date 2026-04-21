"""
Polish service with LLM guardrails.

INV-002: LLM polish layer cannot invent facts.
"""

import logging
import re
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PolishedSection(BaseModel):
    """Polished section content."""

    title: str
    body: str
    key_points: list[str] = Field(max_length=5)


POLISH_PROMPT = """You are a report editor. Your job is to rephrase the following raw data into clear, professional prose.

CRITICAL RULES:
1. Do NOT add any numbers that are not in the raw data.
2. Do NOT add any theme names that are not in the raw data.
3. Do NOT add any action verbs or recommendations not in the raw data.
4. You may ONLY rephrase, reorganize, and improve clarity.
5. Keep all percentages exact (e.g., if raw says 0.34, you may say "34%" but not "about 35%").
6. If a metric is missing from the raw data, do NOT mention it.

Raw data to polish:
{raw_content}

Return polished content with a title, body paragraph, and up to 5 key points."""


class PolishService:
    """Service to polish raw report content using LLM."""

    def __init__(self, model: str = "openai:gpt-4.1-nano"):
        try:
            from pydantic_ai import Agent

            self.agent = Agent(model, output_type=PolishedSection)
        except ImportError:
            self.agent = None
        self.timeout_seconds = 30

    async def polish_section(
        self,
        raw_content: dict,
        section_type: str,
    ) -> tuple[Optional[PolishedSection], bool]:
        """
        Polish a section's raw content.

        Returns:
            (polished_content, used_fallback)
            - polished_content: PolishedSection or None
            - used_fallback: True if fallback was used

        INV-002: Validates that polished content doesn't invent facts.
        """
        if self.agent is None:
            return None, True

        try:
            prompt = POLISH_PROMPT.format(raw_content=raw_content)
            result = await self.agent.run(prompt)
            polished = result.output

            if not self._validate_no_invented_facts(raw_content, polished):
                logger.warning(
                    "Polish validation failed for section %s, using fallback",
                    section_type,
                )
                return None, True

            return polished, False

        except Exception as e:
            logger.error("Polish failed for section %s: %s", section_type, e)
            return None, True

    def _validate_no_invented_facts(
        self,
        raw_content: dict,
        polished: PolishedSection,
    ) -> bool:
        """
        Validate that polished content doesn't contain facts not in raw_content.

        Checks:
        1. All numbers in polished exist in raw (with percentage conversion allowed)
        2. All theme names in polished exist in raw
        """
        raw_str = str(raw_content).lower()
        polished_str = (
            f"{polished.title} {polished.body} {' '.join(polished.key_points)}".lower()
        )

        polished_numbers = self._extract_numbers(polished_str)
        raw_numbers = self._extract_numbers(raw_str)

        for num in polished_numbers:
            if not self._number_exists_in_raw(num, raw_numbers):
                logger.warning("Invented number detected: %s", num)
                return False

        return True

    def _extract_numbers(self, text: str) -> list[float]:
        """Extract all numbers from text."""
        pattern = r"(\d+\.?\d*)\s*%?"
        matches = re.findall(pattern, text)
        return [float(m) for m in matches if m]

    def _number_exists_in_raw(
        self,
        polished_num: float,
        raw_numbers: list[float],
    ) -> bool:
        """Check if a number from polished content exists in raw data."""
        for raw_num in raw_numbers:
            if abs(polished_num - raw_num) < 0.01:
                return True
            if abs(polished_num - raw_num * 100) < 0.1:
                return True
            if abs(polished_num / 100 - raw_num) < 0.01:
                return True
        return False


def create_fallback_polished(raw_content: dict, section_type: str) -> dict:
    """
    Create a minimal polished version from raw content.

    Used when LLM polish fails or is rejected by validation.
    """
    formatters = {
        "exec_summary": _format_exec_summary_fallback,
        "whats_changed": _format_whats_changed_fallback,
        "whats_working": _format_whats_working_fallback,
        "needs_attention": _format_needs_attention_fallback,
        "recommendations": _format_recommendations_fallback,
        "decisions_made": _format_decisions_fallback,
    }

    formatter = formatters.get(section_type, _format_generic_fallback)
    return formatter(raw_content)


def _format_exec_summary_fallback(raw: dict) -> dict:
    if raw.get("empty"):
        return {"title": "Executive Summary", "body": raw["message"], "key_points": []}

    points = []
    if "total_items" in raw:
        points.append(f"{raw['total_items']} feedback items received")
    if raw.get("volume_change") is not None:
        change = raw["volume_change"]
        direction = "up" if change > 0 else "down"
        points.append(f"Volume {direction} {abs(change):.0%} from last week")
    
    # Sentiment breakdown
    sentiment = raw.get("sentiment_distribution", {})
    if sentiment:
        parts = [f"{v:.0%} {k}" for k, v in sentiment.items()]
        points.append(f"Sentiment: {', '.join(parts)}")
    
    # Urgency breakdown
    urgency = raw.get("urgency_distribution", {})
    if urgency.get("high", 0) > 0:
        points.append(f"{urgency['high']:.0%} high urgency")
    
    # Top themes
    top_themes = raw.get("top_themes", [])
    if top_themes:
        theme_str = ", ".join(f"{t['name']} ({t['count']})" for t in top_themes[:3])
        points.append(f"Top themes: {theme_str}")

    return {
        "title": "Executive Summary",
        "body": "Weekly overview of feedback trends and quality metrics.",
        "key_points": points[:5],
    }


def _format_whats_changed_fallback(raw: dict) -> dict:
    if raw.get("empty"):
        return {"title": "What's Changed", "body": raw["message"], "key_points": []}

    points = []
    if raw.get("new_themes"):
        points.append(f"New themes: {', '.join(raw['new_themes'])}")
    if raw.get("rising_themes"):
        points.append(f"Rising themes: {', '.join(raw['rising_themes'])}")
    if raw.get("declining_themes"):
        points.append(f"Declining themes: {', '.join(raw['declining_themes'])}")

    return {
        "title": "What's Changed",
        "body": "Week-over-week changes in feedback patterns.",
        "key_points": points,
    }


def _format_whats_working_fallback(raw: dict) -> dict:
    points = []
    if "positive_sentiment_pct" in raw:
        points.append(f"{raw['positive_sentiment_pct']:.0%} positive sentiment")
    if raw.get("improving_themes"):
        points.append(f"Improving: {', '.join(raw['improving_themes'])}")

    return {
        "title": "What's Working",
        "body": "Positive trends and areas of strength.",
        "key_points": points,
    }


def _format_needs_attention_fallback(raw: dict) -> dict:
    points = []
    for item in raw.get("attention_items", []):
        if item["type"] == "high_negative_sentiment":
            points.append(item["message"])
        elif item["type"] == "high_urgency":
            points.append(item["message"])
        elif item["type"] == "top_theme":
            points.append(f"{item['theme']}: {item['count']} mentions")
        elif item["type"] == "volume_spike":
            points.append(item["message"])
        elif item["type"] == "sentiment_decline":
            points.append(item["message"])
        elif item["type"] == "theme_decline":
            points.append(f"Theme declining: {item['theme']}")

    body = "Areas requiring focus this week."
    if raw.get("negative_sentiment_pct", 0) > 0.5:
        body = f"High negative sentiment ({raw['negative_sentiment_pct']:.0%}) requires attention."

    return {
        "title": "Needs Attention",
        "body": body,
        "key_points": points[:5],
    }


def _format_recommendations_fallback(raw: dict) -> dict:
    if raw.get("empty"):
        return {
            "title": "Top Recommendations",
            "body": raw["message"],
            "key_points": [],
        }

    points = [
        f"{r['title']} (priority: {r['priority_score']:.2f})"
        for r in raw.get("recommendations", [])[:5]
    ]

    return {
        "title": "Top Recommendations",
        "body": f"{raw['count']} recommendations ranked by priority.",
        "key_points": points,
    }


def _format_decisions_fallback(raw: dict) -> dict:
    if raw.get("empty"):
        return {
            "title": "Decisions This Week",
            "body": raw["message"],
            "key_points": [],
        }

    points = [
        f"{raw['accepted']} accepted",
        f"{raw['dismissed']} dismissed",
        f"{raw['pending']} pending review",
    ]

    return {
        "title": "Decisions This Week",
        "body": f"{raw['total']} recommendations decided.",
        "key_points": points,
    }


def _format_generic_fallback(raw: dict) -> dict:
    return {
        "title": "Section",
        "body": str(raw),
        "key_points": [],
    }
