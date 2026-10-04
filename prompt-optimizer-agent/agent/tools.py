"""Tool definitions and implementations for the Prompt Optimizer Agent."""

from typing import Any, Callable, Dict, List, Optional

# Anthropic Tool Schemas
TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "analyze_prompt",
        "description": (
            "Analyzes a user's rough prompt to identify detected intent, target type "
            "(coding / writing / image / data analysis / general), structural missing info, "
            "and improvement recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's rough or candidate prompt to analyze.",
                }
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "test_prompt",
        "description": (
            "Executes the candidate prompt against the LLM with max_tokens=800 to "
            "observe actual LLM response and judge if it fulfills intent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The candidate prompt to run against the LLM.",
                }
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "ask_user",
        "description": (
            "Pauses the optimization loop and asks the user a clarifying question when "
            "critical requirements are ambiguous. Limit to 2 calls per session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The clarifying question to present to the user.",
                }
            },
            "required": ["question"],
        },
    },
    {
        "name": "finalize",
        "description": (
            "Ends the optimization loop with the final structured result JSON object."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "The final result matching the OptimizerResult schema.",
                }
            },
            "required": ["result"],
        },
    },
]


def execute_analyze_prompt(prompt: str, default_target_type: str = "general") -> Dict[str, Any]:
    """Analyze prompt structural elements, target domain, and missing information."""
    prompt_lower = prompt.lower()
    
    # Domain detection fallback heuristics
    target_type = default_target_type
    if any(k in prompt_lower for k in ["code", "python", "javascript", "react", "bug", "function", "api", "sql", "css", "html"]):
        target_type = "coding"
        intent = "Software engineering, code generation, or debugging task"
    elif any(k in prompt_lower for k in ["write", "essay", "article", "blog", "story", "email", "summary", "draft"]):
        target_type = "writing"
        intent = "Textual content creation, writing, or copywriting task"
    elif any(k in prompt_lower for k in ["image", "picture", "logo", "midjourney", "dall-e", "photo", "drawing", "illustration"]):
        target_type = "image"
        intent = "Visual image generation prompt"
    elif any(k in prompt_lower for k in ["data", "csv", "analysis", "statistics", "chart", "pandas", "dataset"]):
        target_type = "data analysis"
        intent = "Data manipulation, statistics, or analytical task"
    else:
        intent = "General task or inquiry"

    missing_info: List[str] = []
    if "role" not in prompt_lower and "act as" not in prompt_lower and "you are" not in prompt_lower:
        missing_info.append("Missing explicit AI role or persona assignment.")
    if len(prompt.split()) < 12:
        missing_info.append("Background context is minimal or brief.")
    if not any(k in prompt_lower for k in ["format", "json", "markdown", "list", "bullet", "table", "output"]):
        missing_info.append("Output format structure is not explicitly specified.")
    if not any(k in prompt_lower for k in ["do not", "must", "constraint", "limit", "only", "never"]):
        missing_info.append("Explicit negative constraints or boundaries are lacking.")

    return {
        "detected_intent": intent,
        "target_type": target_type,
        "missing_information": missing_info if missing_info else ["No major structural elements missing."],
        "word_count": len(prompt.split()),
        "has_role": any(k in prompt_lower for k in ["role", "act as", "you are"]),
        "has_constraints": any(k in prompt_lower for k in ["must", "do not", "never", "limit"]),
        "has_output_format": any(k in prompt_lower for k in ["format", "json", "markdown", "output"]),
    }


def execute_test_prompt(prompt: str, client: Optional[Any], model_name: str) -> Dict[str, Any]:
    """Test candidate prompt against LLM (max_tokens 800)."""
    if client is None:
        # Mock mode if client is not initialized (e.g. testing without API key)
        return {
            "output": (
                f"[Simulated Test Output]\nCandidate prompt tested: '{prompt[:80]}...'\n"
                "Output generated structured output with clear headers and constraints."
            )
        }
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text_content = ""
        for block in response.content:
            if getattr(block, "type", None) == "text":
                text_content += block.text
        return {"output": text_content if text_content else "No text output returned."}
    except Exception as e:
        return {"error": f"LLM prompt test execution failed: {str(e)}"}


def execute_ask_user(question: str, user_input_fn: Optional[Callable[[str], str]] = None) -> Dict[str, Any]:
    """Ask clarifying question to the user in terminal or via callback."""
    if user_input_fn:
        answer = user_input_fn(question)
    else:
        answer = input(f"\n[Agent Clarification Request]: {question}\nYour Answer > ").strip()
    return {"answer": answer}


def dispatch_tool_call(
    tool_name: str,
    tool_args: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Central tool dispatcher catching errors to ensure the loop never crashes."""
    try:
        if tool_name == "analyze_prompt":
            prompt = tool_args.get("prompt", "")
            target_type = context.get("target_type", "general")
            return execute_analyze_prompt(prompt, default_target_type=target_type)

        elif tool_name == "test_prompt":
            prompt = tool_args.get("prompt", "")
            client = context.get("client")
            model_name = context.get("model_name", "claude-3-5-sonnet-20241022")
            return execute_test_prompt(prompt, client, model_name)

        elif tool_name == "ask_user":
            question = tool_args.get("question", "")
            user_input_fn = context.get("user_input_fn")
            return execute_ask_user(question, user_input_fn)

        elif tool_name == "finalize":
            result = tool_args.get("result", {})
            return {"status": "finalized", "result": result}

        else:
            return {"error": f"Unknown tool name: {tool_name}"}

    except Exception as e:
        return {"error": f"Error executing tool '{tool_name}': {str(e)}"}
