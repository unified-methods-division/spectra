"""
Report generation Celery tasks.

INV-007: Report generation never blocks request thread.
"""

import logging

from celery import shared_task
from django.utils import timezone

from reports.models import Report, ReportSection
from reports.services.synthesis import synthesize_report_data, serialize_synthesis_result
from reports.services.sections import assemble_sections
from reports.services.polish import create_fallback_polished
from reports.services.alerts import create_alerts_for_report

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_report_task(self, report_id: str):
    """
    Generate a report asynchronously.

    INV-007: This task runs in Celery, not blocking the API request.
    """
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        logger.error("Report %s not found", report_id)
        return

    try:
        report.status = Report.Status.GENERATING
        report.save(update_fields=["status"])

        logger.info(
            "Synthesizing report %s for tenant %s", report_id, report.tenant_id
        )
        synthesis = synthesize_report_data(
            tenant_id=str(report.tenant_id),
            period_start=report.period_start,
            period_end=report.period_end,
        )

        # Step 3.4: create minimal alerts for drill-down (async side effect ok here)
        try:
            create_alerts_for_report(tenant_id=str(report.tenant_id), synthesis=synthesis)
        except Exception:
            logger.exception("Alert creation failed for report %s (non-fatal)", report_id)

        raw_data = serialize_synthesis_result(synthesis)
        report.raw_data = raw_data
        report.save(update_fields=["raw_data"])

        sections = assemble_sections(report, synthesis)

        for section in sections:
            polished = create_fallback_polished(
                section.raw_content,
                section.section_type,
            )
            section.polished_content = polished

        ReportSection.objects.bulk_create(sections)

        report.status = Report.Status.READY
        report.generated_at = timezone.now()
        report.save(update_fields=["status", "generated_at"])

        logger.info("Report %s generated successfully", report_id)

    except Exception as e:
        logger.exception("Report generation failed for %s", report_id)
        report.status = Report.Status.FAILED
        report.error_message = str(e)
        report.save(update_fields=["status", "error_message"])
        raise self.retry(exc=e, countdown=60)
