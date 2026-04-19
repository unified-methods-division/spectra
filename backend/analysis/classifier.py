from pydantic_ai import Agent, RunContext

from ingestion.models import FeedbackAnalysis

DEFAULT_MODEL = "openai:gpt-4.1-nano"

classifier_agent: Agent[list[str], FeedbackAnalysis] = Agent(
    output_type=FeedbackAnalysis,
    deps_type=list[str],
    instructions=(
        "You are a feedback classifier. For each piece of user feedback:\n"
        "- sentiment: positive, negative, neutral, or mixed\n"
        "- urgency: low, medium, high, or critical\n"
        "- confidence: 0-1 confidence in sentiment\n"
        "- themes: 2-5 topic slugs describing what the feedback is about\n"
        "- summary: 1-2 sentence summary\n\n"
        "THEME RULES:\n"
        "- Use single-word singular nouns when possible: billing, onboarding, export, pricing\n"
        "- Two words max for distinct subtopics: team-invite, csv-export\n"
        "- NO qualifiers like -issues, -bugs, -ux, -problems (sentiment field handles that)\n"
        "- Lowercase, hyphenated\n"
        "- Map to existing taxonomy when possible"
    ),
)

FEW_SHOT_EXAMPLES = """
EXAMPLES:

Feedback: "Your billing page is confusing and I was charged twice"
Output: sentiment=negative, urgency=high, themes=["billing"], summary="User confused by billing page and double-charged"

Feedback: "Love the new onboarding flow, made setup super easy"
Output: sentiment=positive, urgency=low, themes=["onboarding"], summary="User praises improved onboarding experience"

Feedback: "CSV export crashes every time I try to download reports"
Output: sentiment=negative, urgency=high, themes=["export", "crashes"], summary="CSV export feature crashes on download"

Feedback: "Can't figure out how to invite team members"
Output: sentiment=negative, urgency=medium, themes=["onboarding", "collaboration"], summary="User struggling to find team invite functionality"
"""


@classifier_agent.instructions
def inject_few_shot(_ctx: RunContext[list[str]]) -> str:
    return FEW_SHOT_EXAMPLES


@classifier_agent.instructions
def inject_taxonomy(ctx: RunContext[list[str]]) -> str:
    if not ctx.deps:
        return "No existing theme taxonomy. Create new theme slugs as needed."
    return f"Existing theme taxonomy: {', '.join(ctx.deps)}"


def classify_item(
    content: str, theme_slugs: list[str], *, model: str | None = None
) -> FeedbackAnalysis:
    result = classifier_agent.run_sync(
        content, deps=theme_slugs, model=model or DEFAULT_MODEL
    )
    return result.output
