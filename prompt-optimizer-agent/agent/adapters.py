"""Multi-LLM Provider Adapters for Anthropic, OpenAI, Gemini, and Ollama."""

import json
import os
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Normalized tool call structure across all LLM providers."""

    id: str
    name: str
    args: Dict[str, Any]


class LLMResponse(BaseModel):
    """Normalized response structure returned by adapters."""

    text: str = ""
    tool_calls: List[ToolCall] = Field(default_factory=list)


class BaseLLMAdapter(ABC):
    """Abstract Base Class for LLM Provider Adapters."""

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate response given conversation history, system prompt, and tools."""
        pass

    @abstractmethod
    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        """Execute candidate prompt draft in sandbox."""
        pass


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, client: Optional[Any] = None):
        model = model_name or os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
        super().__init__(model_name=model, api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.client = client

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
        from anthropic import Anthropic
        self.client = Anthropic(api_key=self.api_key)
        return self.client

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        client = self._get_client()
        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)
        content_blocks = getattr(response, "content", [])

        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []

        for block in content_blocks:
            b_type = getattr(block, "type", None)
            if b_type == "text":
                text_parts.append(getattr(block, "text", ""))
            elif b_type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=getattr(block, "id", ""),
                        name=getattr(block, "name", ""),
                        args=getattr(block, "input", {}) or {},
                    )
                )

        return LLMResponse(text="\n".join(text_parts), tool_calls=tool_calls)

    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        return "\n".join(text_parts) if text_parts else "No output returned."


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI models (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, client: Optional[Any] = None):
        model = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        super().__init__(model_name=model, api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.client = client

    def _get_client(self) -> Any:
        if self.client is not None:
            return self.client
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        return self.client

    def _format_tools_for_openai(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                }
            })
        return openai_tools

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        client = self._get_client()
        formatted_msgs: List[Dict[str, Any]] = []
        if system:
            formatted_msgs.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, list):
                # Handle Anthropic style message blocks or tool results for OpenAI format
                text_parts = []
                tool_call_results = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        tool_call_results.append(item)
                    elif hasattr(item, "text"):
                        text_parts.append(item.text)
                    elif isinstance(item, str):
                        text_parts.append(item)
                if tool_call_results:
                    for tr in tool_call_results:
                        formatted_msgs.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_use_id", ""),
                            "content": tr.get("content", ""),
                        })
                    continue
                content = "\n".join(text_parts) if text_parts else str(content)
            formatted_msgs.append({"role": role, "content": content})

        kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "messages": formatted_msgs,
        }
        if tools:
            kwargs["tools"] = self._format_tools_for_openai(tools)

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0].message

        text = choice.content or ""
        tool_calls: List[ToolCall] = []

        if choice.tool_calls:
            for tc in choice.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    args=args,
                ))

        return LLMResponse(text=text, tool_calls=tool_calls)

    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or "No output returned."


class GeminiAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini models (gemini-1.5-pro, gemini-2.0-flash, etc.)."""

    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, client: Optional[Any] = None):
        model = model_name or os.getenv("MODEL_NAME", "gemini-1.5-pro")
        super().__init__(model_name=model, api_key=api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        self.client = client

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")

        # Try Google GenAI SDK if installed, otherwise HTTP REST fallback
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            genai_model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system if system else None,
            )

            # Convert prompt messages to string for simplicity in REST/GenAI API
            prompt_str = ""
            if messages:
                last_msg = messages[-1]
                content = last_msg.get("content", "")
                if isinstance(content, list):
                    prompt_str = json.dumps(content)
                else:
                    prompt_str = str(content)

            res = genai_model.generate_content(prompt_str)
            text = res.text if hasattr(res, "text") else str(res)
            return LLMResponse(text=text, tool_calls=[])
        except Exception:
            # Fallback to direct HTTP API call to Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            
            prompt_parts = []
            if system:
                prompt_parts.append(f"System: {system}\n")
            for m in messages:
                prompt_parts.append(f"{m.get('role', 'user')}: {m.get('content', '')}")

            payload = {
                "contents": [{"parts": [{"text": "\n".join(prompt_parts)}]}],
                "generationConfig": {"maxOutputTokens": max_tokens}
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            candidates = result.get("candidates", [])
            text_out = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text_out = "".join(p.get("text", "") for p in parts)

            return LLMResponse(text=text_out, tool_calls=[])

    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        res = self.generate(messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens)
        return res.text or "No output returned."


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for local Ollama models (llama3, mistral, qwen, etc.)."""

    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        model = model_name or os.getenv("MODEL_NAME", "llama3")
        super().__init__(model_name=model)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        formatted_msgs = []
        if system:
            formatted_msgs.append({"role": "system", "content": system})

        for msg in messages:
            content = msg.get("content", "")
            if not isinstance(content, str):
                content = json.dumps(content)
            formatted_msgs.append({"role": msg.get("role", "user"), "content": content})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_msgs,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        if tools:
            # Convert tool definition schema for Ollama format if tool support enabled
            payload["tools"] = tools

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))

            msg_out = res_data.get("message", {})
            text = msg_out.get("content", "")
            raw_tool_calls = msg_out.get("tool_calls", [])

            tool_calls: List[ToolCall] = []
            for i, tc in enumerate(raw_tool_calls):
                func = tc.get("function", {})
                tool_calls.append(ToolCall(
                    id=f"ollama_call_{i+1}",
                    name=func.get("name", ""),
                    args=func.get("arguments", {}) or {},
                ))

            return LLMResponse(text=text, tool_calls=tool_calls)
        except Exception as e:
            return LLMResponse(text=f"[Ollama Error / Connection Failed]: {str(e)}", tool_calls=[])

    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        res = self.generate(messages=[{"role": "user", "content": prompt}], max_tokens=max_tokens)
        return res.text or "No output returned."


class MockAdapter(BaseLLMAdapter):
    """Mock Adapter for fast offline unit testing without API keys."""

    def __init__(self, model_name: str = "mock-model", responses: Optional[List[LLMResponse]] = None):
        super().__init__(model_name=model_name)
        self.responses = responses or []
        self.call_count = 0

    def generate(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if self.call_count < len(self.responses):
            res = self.responses[self.call_count]
            self.call_count += 1
            return res

        # Default fallback mock behavior
        self.call_count += 1
        return LLMResponse(
            text="Mock agent reasoning step.",
            tool_calls=[ToolCall(id="mock_1", name="analyze_prompt", args={"prompt": "test prompt"})],
        )

    def test_prompt(self, prompt: str, max_tokens: int = 800) -> str:
        return f"[Mock Sandbox Execution Output for: '{prompt[:40]}...']"


def get_adapter(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    client: Optional[Any] = None,
) -> BaseLLMAdapter:
    """Factory function to resolve and instantiate the requested provider adapter."""
    provider_name = (provider or os.getenv("MODEL_PROVIDER", "anthropic")).lower().strip()

    if provider_name == "anthropic":
        return AnthropicAdapter(model_name=model_name, api_key=api_key, client=client)
    elif provider_name == "openai":
        return OpenAIAdapter(model_name=model_name, api_key=api_key, client=client)
    elif provider_name == "gemini":
        return GeminiAdapter(model_name=model_name, api_key=api_key, client=client)
    elif provider_name == "ollama":
        return OllamaAdapter(model_name=model_name)
    elif provider_name == "mock":
        return MockAdapter(model_name=model_name or "mock-model")
    else:
        raise ValueError(
            f"Unsupported MODEL_PROVIDER '{provider_name}'. "
            "Supported providers: 'anthropic', 'openai', 'gemini', 'ollama', 'mock'."
        )
