from __future__ import annotations

from .schemas import PromptBlueprint, StructuredIdea

_STEPS_BY_TYPE = {
    "code": [
        "Restate the required feature or fix in one sentence to confirm scope",
        "List tech constraints, edge cases, and success criteria before coding",
        "Produce the solution with clean, idiomatic code and inline reasoning for key decisions",
        "Flag edge cases, failure modes, and how to test the result",
    ],
    "analysis": [
        "Restate the question being analyzed in one sentence",
        "State assumptions and data limits explicitly before concluding anything",
        "Deliver the analysis with evidence, trade-offs, and a clear recommendation",
        "End with what would change the conclusion if new information arrived",
    ],
    "writing": [
        "Restate the piece's purpose, audience, and desired reader reaction in one sentence",
        "Draft with a strong hook, clear structure, and a single core message",
        "Cut every sentence that does not earn its place",
        "Deliver the final draft ready to publish with no placeholders",
    ],
    "marketing": [
        "Restate the offer, audience, and desired action in one sentence",
        "Lead with the strongest benefit, not features",
        "Write the deliverable with clear hooks, social proof slots, and a single call to action",
        "Provide two alternative angles for A/B testing",
    ],
    "planning": [
        "Restate the objective, timeline, and success criteria in one sentence",
        "Break the plan into sequenced phases with owners and dependencies",
        "Surface risks with concrete mitigations",
        "End with a ready-to-use checklist for week one",
    ],
    "learning": [
        "Restate what the learner should be able to do after reading",
        "Explain from first principles with a concrete example before any jargon",
        "Progress from simple to complex in logical steps",
        "Close with a short self-test to confirm understanding",
    ],
    "design": [
        "Restate the user problem, context, and platform constraints in one sentence",
        "Define the core user flow before any visual decisions",
        "Deliver the design rationale with trade-offs made explicit",
        "List concrete next steps (assets, specs, handoff notes)",
    ],
    "general": [
        "Restate the task in one sentence to confirm intent",
        "List assumptions and constraints before solving",
        "Produce a structured response with headings",
        "Validate the answer against goal and audience before finishing",
    ],
}

_QUALITY_BAR = [
    "Specific and concrete; zero generic filler statements",
    "Every claim immediately actionable or evidenced",
    "Matches the audience's knowledge level exactly",
    "No hedging, no disclaimers, no restating the question",
    "If information is missing, state the assumption made and continue",
]


def _clean_fragment(value: str) -> str:
    return value.strip().rstrip(".?!")


def build_blueprint(idea: StructuredIdea) -> PromptBlueprint:
    steps = _STEPS_BY_TYPE.get(idea.task_type, _STEPS_BY_TYPE["general"])
    quality_bar = list(_QUALITY_BAR)

    task_summary = (
        f"{_clean_fragment(idea.goal) or _clean_fragment(idea.problem_statement)}. "
        f"Intended audience: {_clean_fragment(idea.audience)}. "
        f"Deliver as: {_clean_fragment(idea.output_format)}."
    )

    output_schema = [
        "Final Deliverable (complete, copy-paste ready)",
        "Key Decisions / Rationale (3-5 bullets)",
        "Assumptions made (only if any)",
        "Next Actions (2-3 concrete steps)",
    ]

    return PromptBlueprint(
        role=idea.role,
        task_summary=task_summary,
        execution_steps=steps,
        quality_bar=quality_bar,
        output_schema=output_schema,
    )
