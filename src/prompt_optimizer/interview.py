from __future__ import annotations

from .parser import _ROLE_BY_TYPE, _TASK_TYPES, apply_task_type_override, parse_and_analyze
from .planner import build_blueprint
from .renderer import render_optimized_prompt
from .schemas import (
    InterviewOption,
    InterviewPlan,
    InterviewQuestion,
    OptimizationResult,
)

_TYPE_DESCRIPTIONS = {
    "code": "software, apps, scripts, debugging",
    "analysis": "research, comparison, evaluation",
    "writing": "articles, blogs, copy, stories",
    "marketing": "campaigns, ads, growth, SEO",
    "planning": "roadmaps, schedules, strategy",
    "learning": "explainers, tutorials, guides",
    "design": "UI/UX, layouts, prototypes",
    "general": "anything else",
}

_AUDIENCE_OPTIONS = {
    "code": ["Developers / technical team", "End users of the product", "Mixed technical + non-technical"],
    "analysis": ["Executive decision-makers", "Technical peers", "General professional audience"],
    "writing": ["General readers", "Industry professionals", "Existing customers / community"],
    "marketing": ["Potential customers", "Existing customers", "Social media audience"],
    "planning": ["Team members / stakeholders", "Executives", "Clients"],
    "learning": ["Complete beginner", "Intermediate learner", "Advanced practitioner"],
    "design": ["Product team", "End users", "Stakeholders"],
    "general": ["General professional audience", "Technical peers", "Mixed audience"],
}

_OUTPUT_OPTIONS = {
    "code": ["Working code with setup/run instructions", "Code + rationale for key decisions", "Plan first, then code"],
    "analysis": ["Findings + recommendation + evidence", "Executive summary + detailed report", "Comparison table + verdict"],
    "writing": ["Ready-to-publish draft", "Outline + full draft", "Draft + two alternative angles"],
    "marketing": ["Copy + CTA + A/B variants", "Campaign plan + copy", "Hook options + final copy"],
    "planning": ["Phased plan + checklist", "Timeline + owners + risks", "One-page action plan"],
    "learning": ["Explanation + example + self-test", "Step-by-step tutorial", "Beginner-first, jargon-free guide"],
    "design": ["Design + rationale + next steps", "User flow + wireframe description", "Specs ready for handoff"],
    "general": ["Structured response with clear headed sections", "Short answer + supporting detail", "Full report with next actions"],
}

_TONE_OPTIONS = [
    "Direct and practical",
    "Friendly and conversational",
    "Formal and precise",
    "Bold and persuasive",
]

_DEPTH_OPTIONS = [
    ("standard", "Standard — balanced detail"),
    ("quick", "Quick — minimal and skimmable"),
    ("deep", "Deep dive — thorough, edge cases covered"),
]


def _options(values) -> list[InterviewOption]:
    return [InterviewOption(value=v, label=l) for v, l in (x if isinstance(x, tuple) else (x, x) for x in values)]


def _rank_task_types(text: str) -> list[tuple[str, int]]:
    lowered = text.lower()
    ranked = [(t, len([kw for kw in kws if kw in lowered])) for t, kws in _TASK_TYPES]
    ranked.append(("general", 0))
    ranked.sort(key=lambda x: -x[1])
    return ranked


def build_interview(raw_text: str) -> InterviewPlan:
    idea, analysis = parse_and_analyze(raw_text)
    provided = set(analysis.provided_fields)
    questions: list[InterviewQuestion] = []

    if "audience" not in provided:
        opts = _options(_AUDIENCE_OPTIONS.get(idea.task_type, _AUDIENCE_OPTIONS["general"]))
        questions.append(InterviewQuestion(id="audience", prompt="Who is this output for?", options=opts, default=opts[0].value))

    if "output_format" not in provided:
        opts = _options(_OUTPUT_OPTIONS.get(idea.task_type, _OUTPUT_OPTIONS["general"]))
        questions.append(InterviewQuestion(id="output_format", prompt="What form should the final answer take?", options=opts, default=opts[0].value))

    if "tone" not in provided:
        opts = _options(_TONE_OPTIONS)
        questions.append(InterviewQuestion(id="tone", prompt="What tone do you want?", options=opts, default="Direct and practical"))

    if "must_include" not in provided:
        questions.append(
            InterviewQuestion(id="must_include", prompt="Anything that MUST be included? (semicolon-separate multiple; enter = skip)")
        )

    if "constraints" not in provided:
        questions.append(
            InterviewQuestion(id="constraints", prompt="Any hard constraints? (limits, what to avoid; enter = none)")
        )

    opts = _options(_DEPTH_OPTIONS)
    questions.append(InterviewQuestion(id="depth", prompt="How deep should the answer go?", options=opts, default="standard"))

    ranked = _rank_task_types(raw_text)
    detected = idea.task_type
    type_options = [InterviewOption(value="auto", label=f"auto — detected: {detected} ({_TYPE_DESCRIPTIONS.get(detected, 'general')})")]
    seen = {detected}
    for task_type, hits in ranked:
        if len(type_options) >= 4:
            break
        if task_type in seen:
            continue
        if hits == 0 and task_type == "general" and len(type_options) < 4:
            continue
        seen.add(task_type)
        type_options.append(InterviewOption(value=task_type, label=f"{task_type} — {_TYPE_DESCRIPTIONS[task_type]}"))

    return InterviewPlan(detected_type=detected, type_options=type_options, questions=questions, analysis=analysis)


_FIELD_LINES = {
    "audience": "audience",
    "output_format": "output format",
    "tone": "tone",
    "constraints": "constraints",
    "must_include": "must include",
}

_FIELD_LABELS = {
    "audience": "audience pinned",
    "output_format": "output format pinned",
    "tone": "tone pinned",
    "constraints": "constraints added",
    "must_include": "must-include list set",
}


def apply_interview(raw_text: str, answers: dict[str, str], task_type: str = "") -> OptimizationResult:
    answers = {k: (v or "").strip() for k, v in (answers or {}).items()}
    depth = answers.get("depth", "standard")

    additions: list[str] = []
    improvements: list[str] = []
    constraint_parts: list[str] = []

    for field_id, label in _FIELD_LINES.items():
        value = answers.get(field_id, "")
        if not value:
            continue
        if field_id == "constraints":
            constraint_parts.append(value)
        else:
            additions.append(f"{label}: {value}")
        improvements.append(f"{_FIELD_LABELS[field_id]}: {value!r}")

    if depth == "quick":
        constraint_parts.append("Keep the output minimal and skimmable; no filler")
        improvements.append("depth set to quick/minimal")
    elif depth == "deep":
        constraint_parts.append("Be thorough; cover edge cases, trade-offs, and failure modes")
        improvements.append("depth set to deep dive")

    if constraint_parts:
        additions.append(f"constraints: {'; '.join(constraint_parts)}")

    augmented = raw_text.strip()
    if additions:
        augmented = augmented + "\n" + "\n".join(additions)

    idea, analysis = parse_and_analyze(augmented)

    if task_type and task_type != "auto" and apply_task_type_override(idea, task_type):
        improvements.append(f"task type switched: {analysis.task_type} → {task_type}")
        analysis.task_type = task_type

    if not improvements:
        improvements.append("no changes from interview — defaults kept")

    blueprint = build_blueprint(idea)
    optimized_prompt = render_optimized_prompt(idea, blueprint)

    return OptimizationResult(
        structured_idea=idea,
        blueprint=blueprint,
        optimized_prompt=optimized_prompt,
        analysis=analysis,
        improvements_applied=improvements,
    )
