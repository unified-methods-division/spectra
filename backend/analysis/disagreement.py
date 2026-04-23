from django.db import transaction
from django.utils import timezone

from .models import Correction, CorrectionDisagreement


def detect_disagreements_for_item_field(tenant_id: str, feedback_item_id: str, field_corrected: str) -> CorrectionDisagreement | None:
    corrections = list(
        Correction.objects.filter(
            tenant_id=tenant_id,
            feedback_item_id=feedback_item_id,
            field_corrected=field_corrected,
        )
    )

    if not corrections:
        return None

    distinct_values = {c.human_value for c in corrections}

    if len(distinct_values) <= 1:
        CorrectionDisagreement.objects.filter(
            tenant_id=tenant_id,
            feedback_item_id=feedback_item_id,
            field_corrected=field_corrected,
        ).delete()
        return None

    correction_ids = [str(c.id) for c in corrections]

    disagreement, _ = CorrectionDisagreement.objects.update_or_create(
        tenant_id=tenant_id,
        feedback_item_id=feedback_item_id,
        field_corrected=field_corrected,
        defaults={
            "correction_ids": correction_ids,
        },
    )

    return disagreement


def detect_disagreements(tenant_id: str) -> list[CorrectionDisagreement]:
    groups = (
        Correction.objects.filter(tenant_id=tenant_id)
        .values("feedback_item_id", "field_corrected")
        .distinct()
    )

    results = []
    for group in groups:
        d = detect_disagreements_for_item_field(
            tenant_id,
            str(group["feedback_item_id"]),
            group["field_corrected"],
        )
        if d is not None:
            results.append(d)

    return results


def resolve_disagreement(disagreement_id: str, resolved_value, resolved_by: str | None = None) -> CorrectionDisagreement:
    from ingestion.models import FeedbackItem

    with transaction.atomic():
        disagreement = CorrectionDisagreement.objects.select_for_update().get(id=disagreement_id)
        disagreement.resolution_status = CorrectionDisagreement.ResolutionStatus.RESOLVED
        disagreement.resolved_value = resolved_value
        disagreement.resolved_at = timezone.now()
        disagreement.save(update_fields=["resolution_status", "resolved_value", "resolved_at"])

        FeedbackItem.objects.filter(pk=disagreement.feedback_item_id).update(
            **{disagreement.field_corrected: resolved_value}
        )

    disagreement.refresh_from_db()
    return disagreement


def disagreement_rate(tenant_id: str) -> float:
    total_corrections = Correction.objects.filter(tenant_id=tenant_id).count()
    if total_corrections == 0:
        return 0.0

    disagreements_count = CorrectionDisagreement.objects.filter(tenant_id=tenant_id).count()
    return (disagreements_count / total_corrections) * 100