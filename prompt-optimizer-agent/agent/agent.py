"""Main optimization agent loop, step limits, timeout controls, and event emission."""

import json
import os
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .schemas import Event, EventType, OptimizerResult
from .system_prompt import get_system_prompt
from .tools import TOOLS_DEFINITIONS, dispatch_tool_call


def _save_run(result: OptimizerResult) -> str:
    """Save the final result to runs/<timestamp>.json."""
    # Find project runs directory
    base_dir = os.getcwd()
    runs_dir = os.path.join(base_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(runs_dir, f"{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    return filepath


def optimize(
    prompt: str,
    target_type: str = "general",
    tone: str = "detailed",
    on_event: Optional[Callable[[Event], None]] = None,
    client: Optional[Any] = None,
    user_input_fn: Optional[Callable[[str], str]] = None,
) -> OptimizerResult:
    """Main function executing the prompt optimization loop.

    Args:
        prompt: The user's rough starting prompt.
        target_type: Target category ('coding', 'writing', 'image', 'data analysis', 'general').
        tone: Desired prompt tone ('concise', 'detailed', 'step-by-step', 'expert').
        on_event: Optional callback receiving step Event objects.
        client: Optional Anthropic SDK client (allows passing mock clients for tests).
        user_input_fn: Optional function to provide user answer for ask_user calls.

    Returns:
        OptimizerResult: Structured final outcome containing prompt, scores, tips, etc.
    """
    dotenv.load_dotenv()

    start_time = time.time()
    console = Console()
    model_name = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please add it to your .env file or environment."
            )
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

    system_prompt = get_system_prompt(target_type=target_type, tone=tone)

    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": f"Please analyze and optimize this rough prompt:\n\n'{prompt}'",
        }
    ]

    draft_rounds = 0
    ask_user_calls = 0
    step_count = 0
    validation_retry_attempted = False
    final_result: Optional[OptimizerResult] = None

    def emit(event_type: EventType, data: Dict[str, Any], step_num: Optional[int] = None) -> None:
        """Helper to emit events to logger and callback."""
        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.now().isoformat(),
            step=step_num,
        )
        if on_event:
            try:
                on_event(event)
            except Exception:
                pass

    console.print(
        Panel(
            f"[bold cyan]Starting Prompt Optimization[/bold cyan]\n"
            f"[bold yellow]Initial Prompt:[/bold yellow] {prompt}\n"
            f"[bold green]Target Type:[/bold green] {target_type} | [bold green]Tone:[/bold green] {tone}",
            title="Prompt Optimizer Agent",
            border_style="cyan",
        )
    )

    while step_count < 8:
        step_count += 1
        elapsed = time.time() - start_time
        if elapsed > 90.0:
            emit(
                EventType.ERROR,
                {"message": f"Hard timeout of 90 seconds exceeded ({elapsed:.1f}s)"},
                step_count,
            )
            raise TimeoutError(f"Optimization session timed out after {elapsed:.1f} seconds.")

        # At step 8, force model to call finalize
        if step_count == 8:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Maximum LLM step limit (8/8) reached. You MUST call the finalize tool now "
                        "with your best optimized prompt draft and self-assessment scores."
                    ),
                }
            )

        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=TOOLS_DEFINITIONS,
            )
        except Exception as e:
            emit(EventType.ERROR, {"error": str(e)}, step_count)
            raise RuntimeError(f"Anthropic API call failed at step {step_count}: {str(e)}")

        content_blocks = getattr(response, "content", [])

        # Log thinking text
        text_parts = [
            block.text for block in content_blocks if getattr(block, "type", None) == "text"
        ]
        if text_parts:
            combined_text = "\n".join(text_parts)
            console.print(f"[bold blue][Step {step_count}/8 Thinking][/bold blue]\n{combined_text}")
            emit(EventType.THINKING, {"text": combined_text}, step_count)

        tool_use_blocks = [
            block for block in content_blocks if getattr(block, "type", None) == "tool_use"
        ]

        messages.append({"role": "assistant", "content": content_blocks})

        if not tool_use_blocks:
            messages.append(
                {
                    "role": "user",
                    "content": "Please proceed by invoking an appropriate tool (analyze_prompt, test_prompt, ask_user, finalize).",
                }
            )
            continue

        tool_results_content: List[Dict[str, Any]] = []
        finalized_in_this_step = False

        for tool_block in tool_use_blocks:
            tool_name = tool_block.name
            tool_args = tool_block.input
            tool_id = tool_block.id

            console.print(
                f"[bold magenta][Step {step_count} Tool Call][/bold magenta] "
                f"[yellow]{tool_name}[/yellow](args={tool_args})"
            )
            emit(
                EventType.TOOL_CALL,
                {"tool_name": tool_name, "tool_args": tool_args},
                step_count,
            )

            # Rule Enforcements & Dispatching
            if tool_name == "ask_user":
                if ask_user_calls >= 2:
                    tool_res = {
                        "error": (
                            "Maximum ask_user call limit (2) reached for this session. "
                            "Do not ask further questions. Proceed with assumptions marked [assumption]."
                        )
                    }
                else:
                    ask_user_calls += 1
                    question = tool_args.get("question", "")
                    emit(
                        EventType.QUESTION,
                        {"question": question, "call_count": ask_user_calls},
                        step_count,
                    )
                    tool_res = dispatch_tool_call(
                        tool_name, tool_args, {"user_input_fn": user_input_fn}
                    )

            elif tool_name == "test_prompt":
                draft_rounds += 1
                draft_text = tool_args.get("prompt", "")
                console.print(
                    Panel(
                        Syntax(draft_text, "markdown", word_wrap=True),
                        title=f"Draft Candidate (Round {draft_rounds}/3)",
                        border_style="magenta",
                    )
                )
                emit(
                    EventType.DRAFT,
                    {"draft": draft_text, "round": draft_rounds},
                    step_count,
                )

                context_data = {
                    "client": client,
                    "model_name": model_name,
                    "target_type": target_type,
                }
                tool_res = dispatch_tool_call(tool_name, tool_args, context_data)
                if draft_rounds >= 3 and isinstance(tool_res, dict):
                    tool_res["limit_notice"] = (
                        "Maximum 3 draft/test rounds reached. Evaluate output and call finalize."
                    )

            elif tool_name == "finalize":
                raw_result = tool_args.get("result", {})
                if isinstance(raw_result, dict):
                    raw_result["rounds_used"] = max(1, draft_rounds)

                try:
                    validated_res = OptimizerResult.model_validate(raw_result)
                    final_result = validated_res
                    tool_res = {"status": "success", "message": "Result validated successfully."}
                    finalized_in_this_step = True
                except Exception as val_err:
                    if not validation_retry_attempted:
                        validation_retry_attempted = True
                        err_msg = (
                            f"Validation Error in finalize schema: {str(val_err)}. "
                            "Please correct the fields and call finalize again."
                        )
                        console.print(f"[bold red][Schema Validation Error][/bold red] {err_msg}")
                        tool_res = {"error": err_msg}
                        emit(EventType.ERROR, {"validation_error": str(val_err)}, step_count)
                    else:
                        raise ValueError(
                            f"Finalize JSON payload validation failed after retry: {str(val_err)}"
                        )

            else:
                context_data = {
                    "client": client,
                    "model_name": model_name,
                    "target_type": target_type,
                    "user_input_fn": user_input_fn,
                }
                tool_res = dispatch_tool_call(tool_name, tool_args, context_data)

            console.print(
                f"[dim green][Tool Result: {tool_name}][/dim green] {str(tool_res)[:200]}..."
            )
            emit(
                EventType.TOOL_RESULT,
                {"tool_name": tool_name, "result": tool_res},
                step_count,
            )

            tool_results_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(tool_res),
                }
            )

        messages.append({"role": "user", "content": tool_results_content})

        if finalized_in_this_step and final_result is not None:
            console.print(
                Panel(
                    f"[bold green]Optimization Completed![/bold green]\n"
                    f"Overall Score: [bold yellow]{final_result.score.overall}/10[/bold yellow]\n"
                    f"Rounds Used: {final_result.rounds_used} | Steps Used: {step_count}",
                    title="Final Result",
                    border_style="green",
                )
            )
            emit(EventType.FINAL, {"result": final_result.model_dump()}, step_count)
            _save_run(final_result)
            return final_result

        # Early stop if self-score >= 8.0
        if final_result and final_result.score.overall >= 8.0:
            _save_run(final_result)
            return final_result

    if final_result is not None:
        _save_run(final_result)
        return final_result

    raise RuntimeError("Optimization loop reached 8 steps without completing finalization.")
