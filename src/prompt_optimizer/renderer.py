from __future__ import annotations

from .schemas import PromptBlueprint, StructuredIdea


def _numbered(items: list[str]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


def _bullets(items: list[str], fallback: str) -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def render_optimized_prompt(idea: StructuredIdea, blueprint: PromptBlueprint) -> str:
    return (
        "# ROLE\n"
        f"You are a {blueprint.role} operating at the top of your field. "
        "You optimize for precision and usefulness over length.\n\n"
        "# CONTEXT\n"
        f"{idea.problem_statement}\n\n"
        "# OBJECTIVE\n"
        f"{blueprint.task_summary}\n\n"
        "# CONSTRAINTS\n"
        f"{_bullets(idea.constraints, 'Stay within the scope implied by the context')}\n\n"
        "# MUST INCLUDE\n"
        f"{_bullets(idea.must_include, 'The elements essential for the deliverable to be usable')}\n\n"
        "# PROCESS\n"
        f"{_numbered(blueprint.execution_steps)}\n\n"
        "# OUTPUT FORMAT\n"
        f"- Format: {idea.output_format}\n"
        "- Structure the response in exactly this order:\n"
        f"{_numbered(blueprint.output_schema)}\n\n"
        "# QUALITY BAR (verify before responding)\n"
        f"{_bullets(blueprint.quality_bar, 'Specific, actionable, and complete')}\n\n"
        "# TONE\n"
        f"- {idea.tone}\n\n"
        "If any critical information is missing, state your assumption explicitly in one line "
        "under 'Assumptions made', then proceed. Do not ask clarifying questions; deliver the "
        "best possible answer with what you have."
    )
