from __future__ import annotations

from .schemas import PromptBlueprint, StructuredIdea


def _clean_fragment(value: str) -> str:
    return value.strip().rstrip(".?!")


def build_blueprint(idea: StructuredIdea) -> PromptBlueprint:
    execution_steps = [
        "Restate the task in one sentence to confirm intent",
        "List assumptions and constraints before solving",
        "Produce a structured response with headings",
        "Validate the answer against goal and audience",
    ]

    quality_bar = [
        "Specific and concrete, not generic",
        "Aligned with audience knowledge level",
        "Actionable output with next steps",
    ]

    output_schema = [
        "Context Summary",
        "Recommended Approach",
        "Final Output",
        "Quick Self-Check",
    ]

    task_summary = (
        f"Solve: {_clean_fragment(idea.goal)}. "
        f"Audience: {_clean_fragment(idea.audience)}. "
        f"Deliver as: {_clean_fragment(idea.output_format)}."
    )

    return PromptBlueprint(
        task_summary=task_summary,
        execution_steps=execution_steps,
        quality_bar=quality_bar,
        output_schema=output_schema,
    )
