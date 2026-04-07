from pydantic_ai import Agent, RunContext

from ingestion.models import FeedbackAnalysis

DEFAULT_MODEL = "openai:gpt-4.1-nano"

classifier_agent: Agent[list[str], FeedbackAnalysis] = Agent(
    output_type=FeedbackAnalysis,
    deps_type=list[str],
    instructions=(
        "You are a feedback classifier. For each piece of user feedback, determine:\n"
        "- sentiment (positive, negative, neutral, or mixed)\n"
        "- urgency (low, medium, high, or critical)\n"
        "- confidence in your sentiment classification (0-1)\n"
        "- 2-5 theme slugs that describe what the feedback is about\n"
        "- a 1-2 sentence summary\n\n"
        "Map to existing theme slugs when possible. Only create new slugs "
        "(lowercase-hyphenated, 2-4 words) if the feedback genuinely doesn't "
        "fit any existing theme."
    ),
)


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
