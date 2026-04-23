"""
Seed Recommendation rows (+ evidence) for local/demo UX.

Production code never auto-creates recommendations yet; synthesis only reads DB.
Report windows match recommendations by evidence (feedback received in-range), not
by when the Recommendation row was inserted.

Usage:
  uv run python manage.py seed_demo_recommendations
  uv run python manage.py seed_demo_recommendations --tenant-id <uuid>
  uv run python manage.py seed_demo_recommendations --period-start 2026-04-13 --period-end 2026-04-19
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from analysis.models import Recommendation
from core.models import Tenant
from ingestion.models import FeedbackItem
from reports.services.evidence import SelectionCriteria, link_evidence_for_recommendations


def default_report_period(today: date | None = None) -> tuple[date, date]:
    """Match reports.serializers.ReportCreateSerializer default (previous Mon–Sun)."""
    today = today or timezone.localdate()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


class Command(BaseCommand):
    help = (
        "Create demo recommendations (+ evidence) in a report period window. "
        "Recommendations are not auto-generated from feedback in this codebase yet."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=str,
            default=None,
            help="Tenant UUID (default: first tenant by name)",
        )
        parser.add_argument(
            "--period-start",
            type=str,
            default=None,
            help="ISO date (default: same as weekly report default)",
        )
        parser.add_argument(
            "--period-end",
            type=str,
            default=None,
            help="ISO date (default: same as weekly report default)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=3,
            help="Number of recommendations (default 3)",
        )

    def handle(self, *args: Any, **options: Any):
        tenant_id = options["tenant_id"]
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id).first()
            if not tenant:
                self.stderr.write(self.style.ERROR(f"No tenant {tenant_id}"))
                return
        else:
            tenant = Tenant.objects.order_by("name").first()
            if not tenant:
                self.stderr.write(self.style.ERROR("No tenants; create one first."))
                return

        if options["period_start"] and options["period_end"]:
            period_start = date.fromisoformat(options["period_start"])
            period_end = date.fromisoformat(options["period_end"])
        else:
            period_start, period_end = default_report_period()

        count = max(1, min(options["count"], 10))

        items_qs = FeedbackItem.objects.filter(
            tenant=tenant,
            received_at__date__gte=period_start,
            received_at__date__lte=period_end,
        ).order_by("-received_at")

        theme_counts: dict[str, int] = {}
        for item in items_qs[:500]:
            for t in item.themes or []:
                if isinstance(t, str) and t.strip():
                    theme_counts[t.strip()] = theme_counts.get(t.strip(), 0) + 1
        top_themes = sorted(theme_counts.keys(), key=lambda k: -theme_counts[k])[:5]

        templates = [
            (
                "Reduce churn from billing confusion",
                "Customers describe incorrect charges and opaque refund timing.",
                "Audit billing copy + add a one-click receipt breakdown; staff script for refunds.",
            ),
            (
                "Stabilize login / session flows",
                "Reports of unexpected logouts and failed auth on mobile.",
                "Add session telemetry, reproduce on top OS versions, ship a hotfix if needed.",
            ),
            (
                "Improve perceived performance",
                "Latency complaints clustering around core navigation.",
                "Profile LCP on top routes; defer non-critical JS; add skeleton states.",
            ),
        ]

        with transaction.atomic():
            created_ids: list[str] = []
            for i in range(count):
                title, problem, action = templates[i % len(templates)]
                themes_for = (
                    [top_themes[i % len(top_themes)]]
                    if top_themes
                    else ["general"]
                )
                rec = Recommendation.objects.create(
                    tenant=tenant,
                    title=title,
                    problem_statement=problem,
                    proposed_action=action,
                    impact_score=0.75 - (i * 0.05),
                    effort_score=0.35 + (i * 0.05),
                    confidence=0.72 + (i * 0.02),
                    priority_score=0.7,
                    rationale={"themes": themes_for},
                    status=Recommendation.Status.PROPOSED,
                )
                created_ids.append(str(rec.pk))

            fresh = list(
                Recommendation.objects.filter(id__in=created_ids).order_by("created_at")
            )
            criteria = SelectionCriteria(
                max_items=5,
                prefer_recent=True,
                prefer_urgent=True,
                require_theme_match=bool(top_themes),
            )
            n = link_evidence_for_recommendations(fresh, items_qs, criteria=criteria)

        self.stdout.write(
            self.style.SUCCESS(
                f"Tenant {tenant.id}: {len(created_ids)} recommendation(s) "
                f"for {period_start}–{period_end}, {n} evidence link(s). "
                f"Generate weekly report for that period (or use same dates)."
            )
        )
