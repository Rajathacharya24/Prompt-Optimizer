from __future__ import annotations

from .parser import parse_and_analyze
from .planner import build_blueprint
from .renderer import render_optimized_prompt
from .schemas import OptimizationResult


def optimize_raw_idea(raw_text: str) -> OptimizationResult:
    structured_idea, analysis = parse_and_analyze(raw_text)
    blueprint = build_blueprint(structured_idea)
    optimized_prompt = render_optimized_prompt(structured_idea, blueprint)
    return OptimizationResult(
        structured_idea=structured_idea,
        blueprint=blueprint,
        optimized_prompt=optimized_prompt,
        analysis=analysis,
    )
