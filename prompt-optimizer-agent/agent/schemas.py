"""Pydantic models and schemas for the Prompt Optimizer Agent."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Score(BaseModel):
    """Detailed prompt quality scores rated on a scale of 0 to 10."""

    overall: float = Field(..., ge=0.0, le=10.0, description="Overall prompt quality score (0 to 10)")
    clarity: float = Field(..., ge=0.0, le=10.0, description="Clarity and readability score (0 to 10)")
    specificity: float = Field(..., ge=0.0, le=10.0, description="Level of specific detail (0 to 10)")
    context: float = Field(..., ge=0.0, le=10.0, description="Adequacy of background context (0 to 10)")
    constraints: float = Field(..., ge=0.0, le=10.0, description="Quality of defined constraints (0 to 10)")
    output_format: float = Field(..., ge=0.0, le=10.0, description="Definition of expected output structure (0 to 10)")


class OptimizerResult(BaseModel):
    """Structured output returned by the Prompt Optimizer Agent upon finalization."""

    optimized_prompt: str = Field(..., description="The finalized, structured, optimized prompt")
    score: Score = Field(..., description="Detailed numerical breakdown of prompt quality")
    issues: List[str] = Field(default_factory=list, description="Identified weaknesses or missing elements")
    tips: List[str] = Field(..., description="3-6 actionable tips for writing better prompts")
    suggestions: List[str] = Field(default_factory=list, description="Extra ideas, edge cases, or details to add")
    follow_up_questions: List[str] = Field(default_factory=list, description="Optional questions for further prompt tuning")
    rounds_used: int = Field(..., ge=1, description="Total number of draft/testing rounds executed")

    @field_validator("tips")
    @classmethod
    def validate_tips_length(cls, v: List[str]) -> List[str]:
        """Ensure tips contain actionable advice."""
        if not v:
            raise ValueError("Tips list cannot be empty. Provide 3-6 actionable tips.")
        return v


class EventType(str, Enum):
    """Types of events emitted during the optimization loop execution."""

    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    DRAFT = "draft"
    QUESTION = "question"
    FINAL = "final"
    ERROR = "error"


class Event(BaseModel):
    """Event payload emitted to real-time logging and callbacks."""

    event_type: EventType = Field(..., description="Category of event")
    data: Dict[str, Any] = Field(..., description="Associated event payload or details")
    timestamp: str = Field(..., description="ISO 8601 timestamp string when event occurred")
    step: Optional[int] = Field(None, description="Current LLM step number (1-based index)")
