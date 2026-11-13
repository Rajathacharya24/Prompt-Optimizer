from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class StructuredIdea:
    problem_statement: str
    goal: str
    audience: str
    constraints: list[str] = field(default_factory=list)
    output_format: str = "Clear, actionable response"
    tone: str = "Direct and practical"
    must_include: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PromptBlueprint:
    task_summary: str
    execution_steps: list[str]
    quality_bar: list[str]
    output_schema: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OptimizationResult:
    structured_idea: StructuredIdea
    blueprint: PromptBlueprint
    optimized_prompt: str

    def to_dict(self) -> dict:
        return {
            "structured_idea": self.structured_idea.to_dict(),
            "blueprint": self.blueprint.to_dict(),
            "optimized_prompt": self.optimized_prompt,
        }
