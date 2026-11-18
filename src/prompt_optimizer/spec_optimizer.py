from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .parser import parse_and_analyze
from .planner import build_blueprint
from .schemas import PromptAnalysis, PromptBlueprint, StructuredIdea

_DEFAULT_OUTPUT = "Structured response with clear headed sections"
_DEFAULT_TONE = "Direct, practical, and confident"
_DEFAULT_AUDIENCE_CODE = "Technical peers"
_DEFAULT_AUDIENCE_GENERAL = "General professional audience"


@dataclass
class SpecOptimizationResult:
    formatted: str
    optimized_prompt: str
    assumptions: list[str] = field(default_factory=list)
    quick_questions: list[str] = field(default_factory=list)
    vague: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _vague_questions(idea: StructuredIdea, analysis: PromptAnalysis) -> list[str]:
    if analysis.overall_score >= 35 and analysis.word_count >= 8:
        return []
    questions = ["What exact outcome should the prompt produce?"]
    if "audience" not in analysis.provided_fields:
        questions.append("Who is the intended audience?")
    if "output_format" not in analysis.provided_fields:
        questions.append("What output format should the result follow?")
    return questions[:3]


def _build_assumptions(idea: StructuredIdea, analysis: PromptAnalysis) -> list[str]:
    assumptions = list(idea.assumptions)
    if "audience" not in analysis.provided_fields:
        assumptions.append(f"Audience defaulted to '{idea.audience}'")
    if "output_format" not in analysis.provided_fields:
        assumptions.append(f"Output format defaulted to '{idea.output_format}'")
    if "tone" not in analysis.provided_fields:
        assumptions.append(f"Tone set to '{idea.tone}'")
    return assumptions


def _render_core(idea: StructuredIdea, blueprint: PromptBlueprint, raw_text: str) -> str:
    lines = [
        f"Role: You are a {blueprint.role}. Work as a top-tier specialist for this task.",
        "",
        f"Goal: {blueprint.task_summary}",
        "",
        "Context:",
        f"- {idea.problem_statement}",
        f"- Audience: {idea.audience}",
        f"- Task type: {idea.task_type}",
        "- Constraints:",
    ]
    lines.extend(f"  - {item}" for item in idea.constraints)
    lines.extend(
        [
            "",
            "Task steps:",
        ]
    )
    lines.extend(f"{i}. {step}" for i, step in enumerate(blueprint.execution_steps, 1))
    lines.extend(
        [
            "",
            "Rules:",
            "- Keep the user's original intent; never add unrequested goals or features.",
            "- Never invent facts about the user's project.",
            "- Be specific and short. Remove filler words. Use simple, direct language.",
            "- If critical information is missing, state one explicit assumption and proceed.",
            "",
            "Output format:",
            f"- Format: {idea.output_format}",
            "- Structure the response in exactly this order:",
        ]
    )
    lines.extend(f"  {i}. {item}" for i, item in enumerate(blueprint.output_schema, 1))

    example = _extract_example(raw_text)
    if example:
        lines.extend(["", "Example:", f"- {example}"])

    return "\n".join(lines)


def _extract_example(raw_text: str) -> str:
    match = re.search(r"(?:e\.g\.|for example|example)\s*:?\s*([^\n]+)", raw_text, re.I)
    if not match:
        return ""
    value = match.group(1).strip(" .;")
    return value[:180]


def _format_output(core: str, assumptions: list[str]) -> str:
    parts = ["**Optimized Prompt:**", "```", core, "```", ""]
    if assumptions:
        parts.append("**Assumptions:**")
        parts.extend(f"- {item}" for item in assumptions)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def optimize_to_spec(raw_text: str) -> SpecOptimizationResult:
    idea, analysis = parse_and_analyze(raw_text)
    questions = _vague_questions(idea, analysis)
    if questions:
        formatted = "**Quick questions (optional):**\n" + "\n".join(f"- {q}" for q in questions) + "\n"
        return SpecOptimizationResult(
            formatted=formatted,
            optimized_prompt="",
            quick_questions=questions,
            vague=True,
        )

    blueprint = build_blueprint(idea)
    core = _render_core(idea, blueprint, raw_text)
    assumptions = _build_assumptions(idea, analysis)
    return SpecOptimizationResult(
        formatted=_format_output(core, assumptions),
        optimized_prompt=core,
        assumptions=assumptions,
    )
