"""Unit tests for Comparative Benchmark Runner."""

from typing import Any, Dict
from agent.adapters import LLMResponse, MockAdapter, ToolCall
from agent.benchmark import run_benchmark, _compute_output_metrics


def test_compute_output_metrics() -> None:
    """Test calculation of structural output metrics."""
    sample_text = (
        "# Main Title\n\n"
        "Here is the explanation.\n\n"
        "- Point 1\n"
        "- Point 2\n\n"
        "```python\ndef hello():\n    return 'world'\n```\n"
    )
    metrics = _compute_output_metrics(sample_text, latency=0.5)

    assert metrics["latency_sec"] == 0.5
    assert metrics["headers_count"] == 1
    assert metrics["code_blocks_count"] == 1
    assert metrics["bullet_points_count"] == 2
    assert metrics["structure_score"] > 5.0


def test_run_benchmark_with_mock_adapter() -> None:
    """Test full benchmark execution with MockAdapter."""
    finalize_payload = {
        "optimized_prompt": "**Role**: Python Expert\n**Task**: Create API endpoint\n**Output Format**: Markdown code block",
        "score": {
            "overall": 9.0,
            "clarity": 9.0,
            "specificity": 9.0,
            "context": 9.0,
            "constraints": 9.0,
            "output_format": 9.0,
        },
        "issues": [],
        "tips": ["Tip 1", "Tip 2", "Tip 3"],
        "suggestions": ["Suggestion 1"],
        "follow_up_questions": [],
        "rounds_used": 1,
    }

    mock_responses = [
        LLMResponse(
            text="Finalizing prompt optimization.",
            tool_calls=[ToolCall(id="tc1", name="finalize", args={"result": finalize_payload})],
        )
    ]
    adapter = MockAdapter(model_name="mock-benchmark", responses=mock_responses)

    data: Dict[str, Any] = run_benchmark(
        prompt="Build API",
        target_type="coding",
        tone="detailed",
        adapter=adapter,
    )

    assert data["raw_prompt"] == "Build API"
    assert "optimized_prompt" in data
    assert "raw_benchmark" in data
    assert "optimized_benchmark" in data
    assert data["optimizer_result"]["score"]["overall"] == 9.0
