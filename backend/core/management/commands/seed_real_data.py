from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from dateutil.parser import parse as parse_dt
from django.core.management.base import BaseCommand
from django.test import override_settings
from django.utils import timezone

from analysis.disagreement import detect_disagreements_for_item_field
from analysis.improvement import assess_corrections
from analysis.models import (
    Correction,
    GoldSetItem,
    PromptVersion,
    Recommendation,
)
from analysis.outcomes import measure_recommendation_outcome
from analysis.tasks import classify_feedback_batch, embed_feedback_batch
from core.models import Tenant
from google_play_scraper import Sort, reviews
from ingestion.models import FeedbackItem, Source
from reports.models import Report
from reports.services.evidence import SelectionCriteria, link_evidence_for_recommendations
from reports.tasks import generate_report_task
from themes.models import Theme
from themes.tasks import discover_themes_for_source
from trends.engine import compute_daily_accuracy
from trends.models import Alert


def _scrape_reviews(app_id: str, count: int) -> list[dict[str, Any]]:
    result, _ = reviews(app_id, lang="en", country="us", sort=Sort.NEWEST, count=count)
    return [
        {
            "reviewId": r["reviewId"],
            "content": r["content"],
            "userName": r["userName"],
            "at": r["at"],
            "score": r["score"],
        }
        for r in result
    ]


def _load_fixture(fixture_path: str) -> list[dict[str, Any]]:
    p = Path(fixture_path)
    if not p.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    data = json.loads(p.read_text())
    return [
        {
            "reviewId": r["reviewId"],
            "content": r["content"],
            "userName": r["userName"],
            "at": r["at"],
            "score": r["score"],
        }
        for r in data
    ]


def _create_source_and_items(
    tenant: Tenant, reviews: list[dict[str, Any]], source_name: str
) -> tuple[Source, int]:
    source, _ = Source.objects.update_or_create(
        name=source_name,
        tenant=tenant,
        defaults={"source_type": Source.SourceType.API_PULL, "config": {}},
    )
    existing_ids = set(
        FeedbackItem.objects.filter(source=source, external_id__isnull=False).values_list(
            "external_id", flat=True
        )
    )
    new_reviews = [r for r in reviews if r["reviewId"] not in existing_ids]
    items = [
        FeedbackItem(
            tenant=tenant,
            source=source,
            external_id=r["reviewId"],
            content=r["content"],
            author=r["userName"],
            received_at=_parse_received_at(r["at"]),
            metadata={"score": r["score"]},
        )
        for r in new_reviews
    ]
    if items:
        FeedbackItem.objects.bulk_create(items, batch_size=500, ignore_conflicts=True)
    return source, len(items)


def _parse_received_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = parse_dt(value)
    else:
        dt = timezone.now()
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    return dt


def _run_pipeline_sync(source_id: str) -> None:
    with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
        classify_feedback_batch.apply(args=(source_id,))
        embed_feedback_batch.apply(args=(source_id,))
        discover_themes_for_source.apply(args=(source_id,))


def _default_report_period(today: date | None = None) -> tuple[date, date]:
    from datetime import timedelta

    today = today or timezone.localdate()
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def _seed_corrections(tenant: Tenant, items: list[FeedbackItem]) -> int:
    classified = [i for i in items if i.processed_at is not None][:15]
    if not classified:
        return 0

    count = 0

    for idx, item in enumerate(classified):
        if idx < 5:
            ai_val = "neutral"
            human_val = "negative"
            Correction.objects.create(
                feedback_item=item,
                tenant=tenant,
                field_corrected=Correction.CorrectedField.SENTIMENT,
                ai_value=ai_val,
                human_value=human_val,
            )
            FeedbackItem.objects.filter(pk=item.pk).update(sentiment=human_val)
            detect_disagreements_for_item_field(str(tenant.id), str(item.pk), "sentiment")
            count += 1
        elif idx < 7:
            ai_val = item.sentiment or "neutral"
            human_val = "neutral" if ai_val == "negative" else "negative"
            Correction.objects.create(
                feedback_item=item,
                tenant=tenant,
                field_corrected=Correction.CorrectedField.SENTIMENT,
                ai_value=ai_val,
                human_value=human_val,
            )
            FeedbackItem.objects.filter(pk=item.pk).update(sentiment=human_val)
            detect_disagreements_for_item_field(str(tenant.id), str(item.pk), "sentiment")
            count += 1
        elif idx < 11:
            ai_val = item.urgency or "medium"
            human_val = "high" if ai_val != "high" else "medium"
            Correction.objects.create(
                feedback_item=item,
                tenant=tenant,
                field_corrected=Correction.CorrectedField.URGENCY,
                ai_value=ai_val,
                human_value=human_val,
            )
            FeedbackItem.objects.filter(pk=item.pk).update(urgency=human_val)
            detect_disagreements_for_item_field(str(tenant.id), str(item.pk), "urgency")
            count += 1
        else:
            ai_themes = list(item.themes) if item.themes else ["general"]
            human_themes = list(set(ai_themes + ["stability"])) if "stability" not in ai_themes else ai_themes[:-1]
            Correction.objects.create(
                feedback_item=item,
                tenant=tenant,
                field_corrected=Correction.CorrectedField.THEMES,
                ai_value=ai_themes,
                human_value=human_themes,
            )
            FeedbackItem.objects.filter(pk=item.pk).update(themes=human_themes)
            try:
                detect_disagreements_for_item_field(str(tenant.id), str(item.pk), "themes")
            except TypeError:
                pass
            count += 1

    return count


def _seed_gold_set(tenant: Tenant, items: list[FeedbackItem]) -> int:
    classified = [i for i in items if i.processed_at is not None][:10]
    if not classified:
        return 0

    count = 0
    for item in classified:
        score = (item.metadata or {}).get("score", 3)
        if score <= 2:
            gold_sent = "negative"
        elif score >= 4:
            gold_sent = "positive"
        else:
            gold_sent = "neutral"

        gold_urg = "high" if score <= 1 else ("medium" if score <= 3 else "low")
        gold_themes = item.themes if item.themes else ["general"]

        _, created = GoldSetItem.objects.update_or_create(
            tenant=tenant,
            feedback_item=item,
            defaults={
                "gold_sentiment": gold_sent,
                "gold_urgency": gold_urg,
                "gold_themes": gold_themes,
            },
        )
        if created:
            count += 1

    return count


def _run_improvement(tenant_id: str) -> PromptVersion | None:
    pv = assess_corrections(tenant_id)
    return pv


def _seed_snapshots(tenant_id: str, days: int = 14) -> int:
    today = date.today()
    count = 0
    for i in range(days, 0, -1):
        snap_date = today - timedelta(days=i)
        compute_daily_accuracy(tenant_id, snap_date)
        count += 1
    return count


def _seed_report_and_alerts(
    tenant: Tenant, period_start: date, period_end: date, async_mode: bool = False
) -> tuple[Report, int]:
    from reports.models import ReportSection

    report, created = Report.objects.update_or_create(
        tenant=tenant,
        report_type=Report.ReportType.WEEKLY_OUTLOOK,
        period_start=period_start,
        period_end=period_end,
        defaults={"status": Report.Status.PENDING, "raw_data": None},
    )
    if not created:
        ReportSection.objects.filter(report=report).delete()
    if async_mode:
        generate_report_task.delay(str(report.id))
    else:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            generate_report_task.apply(args=(str(report.id),))
    alert_count = Alert.objects.filter(tenant=tenant).count()
    return report, alert_count


def _seed_recommendations(
    tenant: Tenant,
    items_qs: Any,
    period_start: date,
    period_end: date,
) -> list[Recommendation]:
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

    theme_counts: dict[str, int] = {}
    for item in items_qs[:500]:
        for t in item.themes or []:
            if isinstance(t, str) and t.strip():
                theme_counts[t.strip()] = theme_counts.get(t.strip(), 0) + 1
    top_themes = sorted(theme_counts.keys(), key=lambda k: -theme_counts[k])[:5]

    recs: list[Recommendation] = []
    for i, (title, problem, action) in enumerate(templates):
        themes_for = [top_themes[i % len(top_themes)]] if top_themes else ["general"]
        rec, created = Recommendation.objects.update_or_create(
            tenant=tenant,
            title=title,
            defaults={
                "problem_statement": problem,
                "proposed_action": action,
                "impact_score": 0.75 - (i * 0.05),
                "effort_score": 0.35 + (i * 0.05),
                "confidence": 0.72 + (i * 0.02),
                "priority_score": 0.7,
                "rationale": {"themes": themes_for},
                "status": Recommendation.Status.PROPOSED,
            },
        )
        recs.append(rec)

    needs_evidence = [r for r in recs if not r.evidence.exists()]
    if needs_evidence:
        criteria = SelectionCriteria(
            max_items=5,
            prefer_recent=True,
            prefer_urgent=True,
            require_theme_match=bool(top_themes),
        )
        link_evidence_for_recommendations(needs_evidence, items_qs, criteria=criteria)

    return recs


def _seed_outcomes(tenant: Tenant, recommendations: list[Recommendation]) -> int:
    if not recommendations:
        return 0
    rec = recommendations[0]
    rec.status = Recommendation.Status.ACCEPTED
    rec.decided_at = timezone.now()
    rec.save(update_fields=["status", "decided_at"])
    outcomes = measure_recommendation_outcome(str(rec.id))
    return len(outcomes)


def _reset_data() -> None:
    from django.db import transaction

    from analysis.models import Correction, CorrectionDisagreement, GoldSetItem, PromptVersion, Recommendation, RecommendationEvidence, RecommendationOutcome
    from reports.models import Report, ReportSection
    from themes.models import Theme
    from trends.models import Alert, TrendSnapshot

    with transaction.atomic():
        RecommendationOutcome.objects.all().delete()
        RecommendationEvidence.objects.all().delete()
        ReportSection.objects.all().delete()
        Report.objects.all().delete()
        Recommendation.objects.all().delete()
        Correction.objects.all().delete()
        CorrectionDisagreement.objects.all().delete()
        GoldSetItem.objects.all().delete()
        PromptVersion.objects.all().delete()
        Alert.objects.all().delete()
        TrendSnapshot.objects.all().delete()
        Theme.objects.all().delete()
        FeedbackItem.objects.all().delete()
        Source.objects.all().delete()


class Command(BaseCommand):
    help = "Seed real Google Play review data and run the full analysis pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id", type=str, default=None, help="Tenant UUID (default: first tenant by name)"
        )
        parser.add_argument("--app-id", type=str, default="com.Slack", help="Google Play app ID")
        parser.add_argument("--count", type=int, default=200, help="Number of reviews to scrape")
        parser.add_argument("--fixture", type=str, default=None, help="Path to JSON fixture (skips scraping)")
        parser.add_argument("--period-start", type=str, default=None, help="ISO date for report period start")
        parser.add_argument("--period-end", type=str, default=None, help="ISO date for report period end")
        parser.add_argument("--reset", action="store_true", default=False, help="Delete all data before seeding")
        parser.add_argument("--dry-run", action="store_true", default=False, help="Show what would be seeded without writing to DB")
        parser.add_argument("--async", action="store_true", dest="async_mode", default=False, help="Use Celery async tasks instead of synchronous")

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

        if options["reset"]:
            self.stdout.write(self.style.WARNING("Resetting all data..."))
            _reset_data()
            self.stdout.write(self.style.SUCCESS("Reset complete"))

        if options["period_start"] and options["period_end"]:
            period_start = date.fromisoformat(options["period_start"])
            period_end = date.fromisoformat(options["period_end"])
        else:
            period_start, period_end = _default_report_period()

        fixture_path = options["fixture"]
        if fixture_path:
            self.stdout.write(self.style.SUCCESS(f"Loading fixture from {fixture_path}"))
            review_data = _load_fixture(fixture_path)
        else:
            app_id = options["app_id"]
            count = options["count"]
            self.stdout.write(self.style.SUCCESS(f"Scraping {count} reviews for {app_id}"))
            review_data = _scrape_reviews(app_id, count)

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(review_data)} reviews"))

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Would create {len(review_data)} items for tenant {tenant.name}"))
            return

        source_name = f"Google Play: {options['app_id']}"
        self.stdout.write(self.style.SUCCESS(f"Creating source + items: {source_name}"))
        source, created_count = _create_source_and_items(tenant, review_data, source_name)
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} new feedback items"))

        if options["async_mode"]:
            from analysis.tasks import process_source
            process_source.delay(str(source.id))
            self.stdout.write(self.style.SUCCESS(f"Pipeline dispatched async for source {source.id}"))
            self.stdout.write(self.style.WARNING("Async mode: downstream seeding skipped (items not yet processed)"))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. Tenant {tenant.id}: {created_count} items queued, "
                    f"period {period_start}–{period_end}."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Running pipeline for source {source.id}"))
        _run_pipeline_sync(str(source.id))
        self.stdout.write(self.style.SUCCESS("Pipeline complete (classify > embed > discover)"))

        all_items = list(FeedbackItem.objects.filter(tenant=tenant))
        self.stdout.write(self.style.SUCCESS("Seeding corrections..."))
        corrections_count = _seed_corrections(tenant, all_items)
        self.stdout.write(self.style.SUCCESS(f"Created {corrections_count} corrections"))

        self.stdout.write(self.style.SUCCESS("Seeding gold set..."))
        gold_count = _seed_gold_set(tenant, all_items)
        self.stdout.write(self.style.SUCCESS(f"Created {gold_count} gold set items"))

        self.stdout.write(self.style.SUCCESS("Running improvement loop..."))
        pv = _run_improvement(str(tenant.id))
        if pv:
            self.stdout.write(self.style.SUCCESS(f"PromptVersion v{pv.version} created (active={pv.active})"))
        else:
            self.stdout.write(self.style.WARNING("No improvement pattern threshold met"))

        self.stdout.write(self.style.SUCCESS("Seeding 14-day trend snapshots..."))
        snap_count = _seed_snapshots(str(tenant.id), days=14)
        self.stdout.write(self.style.SUCCESS(f"Created {snap_count} trend snapshots"))

        items_qs = FeedbackItem.objects.filter(tenant=tenant).order_by("-received_at")
        self.stdout.write(self.style.SUCCESS("Seeding recommendations..."))
        recs = _seed_recommendations(tenant, items_qs, period_start, period_end)
        self.stdout.write(self.style.SUCCESS(f"Created {len(recs)} recommendations"))

        self.stdout.write(self.style.SUCCESS("Seeding report + alerts..."))
        report, alert_count = _seed_report_and_alerts(tenant, period_start, period_end, async_mode=options["async_mode"])
        self.stdout.write(self.style.SUCCESS(f"Report {report.id}: {alert_count} alerts"))

        self.stdout.write(self.style.SUCCESS("Seeding outcomes..."))
        outcome_count = _seed_outcomes(tenant, recs)
        self.stdout.write(self.style.SUCCESS(f"Created {outcome_count} outcomes"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Tenant {tenant.id}: "
                f"{FeedbackItem.objects.filter(tenant=tenant).count()} items, "
                f"{Theme.objects.filter(tenant=tenant).count()} themes, "
                f"{Correction.objects.filter(tenant=tenant).count()} corrections, "
                f"{Alert.objects.filter(tenant=tenant).count()} alerts, "
                f"{Recommendation.objects.filter(tenant=tenant).count()} recommendations, "
                f"period {period_start}–{period_end}."
            )
        )