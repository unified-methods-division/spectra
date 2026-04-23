from datetime import date, datetime, time, timedelta
from django.utils import timezone
from analysis.eval import run_gold_eval
from analysis.models import Correction, PromptVersion
from trends.engine import measure_accuracy
from collections import defaultdict

DEFAULT_ASSESSMENT_WINDOW = timedelta(days=7)


def assess_corrections(
    tenant_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    assessment_window: timedelta = DEFAULT_ASSESSMENT_WINDOW,
) -> PromptVersion | None:
    """Assess corrections for patterns and create improved prompt instructions for the AI."""

    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - assessment_window

    corrections = (
        Correction.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=timezone.make_aware(datetime.combine(start_date, time.min)),
            created_at__lte=timezone.make_aware(datetime.combine(end_date, time.max)),
        )
        .order_by("created_at")
    )

    # loop through corrections and store the occurence of items sharing the same field, human value and ai value
    occurrences: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    for correction in corrections:
        key = (
            correction.field_corrected,
            correction.human_value,
            correction.ai_value,
        )
        occurrences[key] += 1

    # improvement candidates are corrections with occurrences >= 5
    improvement_candidates = [key for key, count in occurrences.items() if count >= 5]

    if not improvement_candidates:
        return None

    # pick ~3 samples from each group
    sample_corrections = [
        corrections.filter(
            field_corrected=field, human_value=human_value, ai_value=ai_value
        ).order_by("created_at")[:3]
        for field, human_value, ai_value in improvement_candidates
    ]

    # build new prompt instructions for the AI
    new_prompt_instructions = []
    for correction in sample_corrections:
        # Convert to few-shot examples for the prompt instructions.
        for c in correction:
            # Assume 'feedback_item' is a FK and it has a 'content' field containing the AI input
            new_prompt_instructions.append(
                {
                    "field": c.field_corrected,
                    "input_text": getattr(c.feedback_item, "content", None),
                    "ai_prediction": c.ai_value,
                    "user_correction": c.human_value,
                    "target": c.human_value,
                }
            )
    prompt_template = "When the user corrects {field} to {human_value}, the AI should predict {human_value}."
    # save new prompt instructions to the database
    prompt_version = PromptVersion.objects.create(
        tenant_id=tenant_id,
        version=PromptVersion.objects.filter(tenant_id=tenant_id).count() + 1,
        few_shot_examples=new_prompt_instructions,
        prompt_template=prompt_template,
    )

    # measure the accuracy of the new prompt instructions
    # I don't think we have the infra setup for accuracy comparison at the correction level
    accuracy = measure_accuracy(
        tenant_id,
        snapshot_date=end_date,
        new_prompt_version=prompt_version,
        corrections=sample_corrections,
    )
    prompt_version.accuracy_at_creation = accuracy
    prompt_version.save()

    previous_prompt_version = (
        PromptVersion.objects.filter(
            tenant_id=tenant_id, version__lt=prompt_version.version
        )
        .order_by("-version")
        .first()
    )

    gold_result = run_gold_eval(tenant_id)

    if gold_result.items_evaluated > 0:
        prompt_version.accuracy_at_creation = gold_result.overall_accuracy
        prompt_version.save()

        if previous_prompt_version and previous_prompt_version.accuracy_current is not None:
            if gold_result.overall_accuracy < previous_prompt_version.accuracy_current:
                prompt_version.regression_note = (
                    f"Gold-set eval accuracy {gold_result.overall_accuracy:.4f}"
                    f" < previous {previous_prompt_version.accuracy_current:.4f}"
                )
                prompt_version.active = False
                prompt_version.save()
                return prompt_version

    if (
        not previous_prompt_version
        or previous_prompt_version.accuracy_current is None
        or accuracy > previous_prompt_version.accuracy_current
    ):
        prompt_version.active = True
        prompt_version.save()
        if previous_prompt_version:
            previous_prompt_version.active = False
            previous_prompt_version.save()

    return prompt_version
