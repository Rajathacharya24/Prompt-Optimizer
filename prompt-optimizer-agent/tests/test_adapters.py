"""Unit tests for Multi-LLM provider adapters."""

from unittest.mock import MagicMock
import pytest

from agent.adapters import (
    AnthropicAdapter,
    BaseLLMAdapter,
    GeminiAdapter,
    LLMResponse,
    MockAdapter,
    OllamaAdapter,
    OpenAIAdapter,
    ToolCall,
    get_adapter,
)


def test_get_adapter_factory() -> None:
    """Test factory resolution of provider adapters."""
    anthropic_ad = get_adapter(provider="anthropic")
    assert isinstance(anthropic_ad, AnthropicAdapter)

    openai_ad = get_adapter(provider="openai")
    assert isinstance(openai_ad, OpenAIAdapter)

    gemini_ad = get_adapter(provider="gemini")
    assert isinstance(gemini_ad, GeminiAdapter)

    ollama_ad = get_adapter(provider="ollama")
    assert isinstance(ollama_ad, OllamaAdapter)

    mock_ad = get_adapter(provider="mock")
    assert isinstance(mock_ad, MockAdapter)

    with pytest.raises(ValueError, match="Unsupported MODEL_PROVIDER"):
        get_adapter(provider="unknown_provider")


def test_mock_adapter_generate_and_test() -> None:
    """Test MockAdapter response generation and sandbox testing."""
    custom_responses = [
        LLMResponse(
            text="Thinking step 1",
            tool_calls=[ToolCall(id="tc1", name="analyze_prompt", args={"prompt": "Write a python app"})],
        ),
        LLMResponse(
            text="Finalizing step",
            tool_calls=[ToolCall(id="tc2", name="finalize", args={"result": {"optimized_prompt": "Final prompt"}})],
        ),
    ]
    adapter = MockAdapter(model_name="mock-v1", responses=custom_responses)

    res1 = adapter.generate(messages=[{"role": "user", "content": "hi"}])
    assert res1.text == "Thinking step 1"
    assert res1.tool_calls[0].name == "analyze_prompt"

    res2 = adapter.generate(messages=[{"role": "user", "content": "next"}])
    assert res2.text == "Finalizing step"
    assert res2.tool_calls[0].name == "finalize"

    test_output = adapter.test_prompt("Write code")
    assert "[Mock Sandbox Execution Output" in test_output


def test_openai_adapter_formatting() -> None:
    """Test OpenAIAdapter tool schema transformation."""
    adapter = OpenAIAdapter(model_name="gpt-4o", api_key="dummy-key")
    tools = [
        {
            "name": "analyze_prompt",
            "description": "Analyze raw prompt",
            "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}}},
        }
    ]
    formatted = adapter._format_tools_for_openai(tools)
    assert len(formatted) == 1
    assert formatted[0]["type"] == "function"
    assert formatted[0]["function"]["name"] == "analyze_prompt"
