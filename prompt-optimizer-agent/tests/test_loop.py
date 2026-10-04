"""Unit tests for the Prompt Optimizer Agent loop and tool handling.

All tests mock the Anthropic SDK client and run without making real API calls.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock
import pytest

from agent.agent import optimize
from agent.schemas import Event, EventType, OptimizerResult


class MockTextBlock:
    """Mock text block in Anthropic response."""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class MockToolUseBlock:
    """Mock tool_use block in Anthropic response."""

    def __init__(self, tool_id: str, tool_name: str, tool_input: Dict[str, Any]):
        self.type = "tool_use"
        self.id = tool_id
        self.name = tool_name
        self.input = tool_input


class MockResponse:
    """Mock response returned by client.messages.create."""

    def __init__(self, content: List[Any]):
        self.content = content


def create_valid_finalize_payload(overall_score: float = 8.5) -> Dict[str, Any]:
    """Helper to generate a valid finalize JSON payload."""
    return {
        "optimized_prompt": (
            "**Role**: Expert Python Developer\n\n"
            "**Context**: You are building a CLI application in Python 3.11.\n\n"
            "**Task**: Write clean code with type hints.\n\n"
            "**Constraints**: No third-party frameworks [assumption].\n\n"
            "**Output Format**: Code blocks with comments."
        ),
        "score": {
            "overall": overall_score,
            "clarity": 9.0,
            "specificity": 8.5,
            "context": 8.0,
            "constraints": 8.5,
            "output_format": 9.0,
        },
        "issues": ["Minor brevity in context."],
        "tips": [
            "Assign explicit expert role at the start.",
            "Use markdown headers for clear sectioning.",
            "Specify exact output structure and format expectations.",
        ],
        "suggestions": ["Add unit tests with pytest."],
        "follow_up_questions": ["What Python version is targeted?"],
        "rounds_used": 1,
    }


def test_early_stop() -> None:
    """Test that the loop stops early when agent score is >= 8.0."""
    mock_client = MagicMock()

    # Step 1: analyze_prompt -> Step 2: test_prompt -> Step 3: finalize (score=9.0)
    response_1 = MockResponse([
        MockTextBlock("Analyzing user prompt..."),
        MockToolUseBlock("call_1", "analyze_prompt", {"prompt": "Write a python function"}),
    ])
    response_2 = MockResponse([
        MockTextBlock("Testing draft candidate..."),
        MockToolUseBlock("call_2", "test_prompt", {"prompt": "Role: Python Expert\nTask: Write function"}),
    ])
    response_3 = MockResponse([
        MockTextBlock("Score is 9.0 >= 8.0, finalizing optimization."),
        MockToolUseBlock("call_3", "finalize", {"result": create_valid_finalize_payload(overall_score=9.0)}),
    ])

    mock_client.messages.create.side_effect = [response_1, response_2, response_3]

    events: List[Event] = []

    result = optimize(
        prompt="Write a python function",
        target_type="coding",
        tone="detailed",
        on_event=events.append,
        client=mock_client,
    )

    assert isinstance(result, OptimizerResult)
    assert result.score.overall == 9.0
    assert result.rounds_used >= 1
    assert any(e.event_type == EventType.FINAL for e in events)
    assert mock_client.messages.create.call_count == 3


def test_step_limit() -> None:
    """Test that the loop forces finalization upon reaching max steps (8)."""
    mock_client = MagicMock()

    # 7 analysis steps followed by a final step calling finalize
    responses = []
    for i in range(1, 8):
        responses.append(
            MockResponse([
                MockTextBlock(f"Step {i} analysis"),
                MockToolUseBlock(f"call_{i}", "analyze_prompt", {"prompt": f"Draft iteration {i}"}),
            ])
        )
    # Step 8 response calls finalize
    responses.append(
        MockResponse([
            MockTextBlock("Step 8 limit reached, submitting finalize call."),
            MockToolUseBlock("call_8", "finalize", {"result": create_valid_finalize_payload(overall_score=7.5)}),
        ])
    )

    mock_client.messages.create.side_effect = responses

    result = optimize(
        prompt="Create a REST API endpoint",
        target_type="coding",
        client=mock_client,
    )

    assert isinstance(result, OptimizerResult)
    assert mock_client.messages.create.call_count == 8


def test_tool_error_handling() -> None:
    """Test that tool execution errors are caught and returned to model as tool results without crashing."""
    mock_client = MagicMock()

    # Exceed ask_user limit (> 2 calls) to trigger tool restriction error result
    resp_1 = MockResponse([
        MockToolUseBlock("c1", "ask_user", {"question": "Q1: What framework?"}),
    ])
    resp_2 = MockResponse([
        MockToolUseBlock("c2", "ask_user", {"question": "Q2: What database?"}),
    ])
    resp_3 = MockResponse([
        MockToolUseBlock("c3", "ask_user", {"question": "Q3: Should fail limit?"}),
    ])
    resp_4 = MockResponse([
        MockToolUseBlock("c4", "finalize", {"result": create_valid_finalize_payload()}),
    ])

    mock_client.messages.create.side_effect = [resp_1, resp_2, resp_3, resp_4]

    def mock_user_input(q: str) -> str:
        return "FastAPI"

    result = optimize(
        prompt="Build a web backend",
        target_type="coding",
        client=mock_client,
        user_input_fn=mock_user_input,
    )

    assert isinstance(result, OptimizerResult)
    assert mock_client.messages.create.call_count == 4


def test_invalid_json_retry() -> None:
    """Test that invalid finalize JSON schema triggers validation error retry once."""
    mock_client = MagicMock()

    # Step 1: finalize call with INVALID payload (missing 'tips')
    invalid_payload = create_valid_finalize_payload()
    del invalid_payload["tips"]  # violates Pydantic schema requirement

    resp_1 = MockResponse([
        MockToolUseBlock("call_bad", "finalize", {"result": invalid_payload}),
    ])

    # Step 2: finalize call with VALID payload after error message feedback
    valid_payload = create_valid_finalize_payload(overall_score=8.8)
    resp_2 = MockResponse([
        MockToolUseBlock("call_good", "finalize", {"result": valid_payload}),
    ])

    mock_client.messages.create.side_effect = [resp_1, resp_2]

    events: List[Event] = []

    result = optimize(
        prompt="Write a poem",
        target_type="writing",
        on_event=events.append,
        client=mock_client,
    )

    assert isinstance(result, OptimizerResult)
    assert result.score.overall == 8.8
    assert any(e.event_type == EventType.ERROR for e in events)
    assert mock_client.messages.create.call_count == 2
