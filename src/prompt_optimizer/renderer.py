from __future__ import annotations

from .schemas import PromptBlueprint, StructuredIdea


def _render_list(items: list[str], fallback: str) -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def render_optimized_prompt(idea: StructuredIdea, blueprint: PromptBlueprint) -> str:
    return (
        "You are an expert assistant focused on producing high-quality outputs.\n\n"
        "Task\n"
        f"- {blueprint.task_summary}\n"
        f"- Core problem: {idea.problem_statement}\n\n"
        "Audience\n"
        f"- {idea.audience}\n\n"
        "Constraints\n"
        f"{_render_list(idea.constraints, 'Respect implied constraints from context')}\n\n"
        "Must Include\n"
        f"{_render_list(idea.must_include, 'Include key points needed for decision-making')}\n\n"
        "Execution Steps\n"
        f"{_render_list(blueprint.execution_steps, 'Provide a complete answer')}\n\n"
        "Quality Bar\n"
        f"{_render_list(blueprint.quality_bar, 'Ensure output quality before finishing')}\n\n"
        "Output Format\n"
        f"- {idea.output_format}\n"
        "- Use this section order:\n"
        f"{_render_list(blueprint.output_schema, 'Final Output')}\n\n"
        "Tone\n"
        f"- {idea.tone}\n"
    )
