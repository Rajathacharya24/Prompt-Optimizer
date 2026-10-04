"""Command Line Interface for Prompt Optimizer Agent."""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

from .agent import optimize
from .schemas import OptimizerResult


def main() -> None:
    """CLI entry point for prompt optimization."""
    parser = argparse.ArgumentParser(
        description="Prompt Optimizer Agent - Iteratively refine AI prompts with LLM tool use."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="The rough prompt string to optimize. If omitted, launches interactive mode.",
    )
    parser.add_argument(
        "--type",
        dest="target_type",
        choices=["coding", "writing", "image", "data analysis", "general"],
        default="general",
        help="Target prompt domain category (default: general).",
    )
    parser.add_argument(
        "--tone",
        choices=["concise", "detailed", "step-by-step", "expert"],
        default="detailed",
        help="Desired tone/style of optimized prompt (default: detailed).",
    )

    args = parser.parse_args()
    console = Console()

    # Interactive mode prompt collection if positional prompt is not provided
    input_prompt = args.prompt
    target_type = args.target_type
    tone = args.tone

    if not input_prompt:
        console.print(
            Panel(
                "[bold cyan]Prompt Optimizer Agent - Interactive Console[/bold cyan]\n"
                "Refine rough prompt ideas into structured, high-performing prompts.",
                border_style="cyan",
            )
        )
        input_prompt = Prompt.ask("[bold yellow]Enter your rough prompt[/bold yellow]")
        if not input_prompt.strip():
            console.print("[bold red]Error:[/bold red] Prompt cannot be empty.")
            sys.exit(1)

        target_type = Prompt.ask(
            "[bold green]Select Target Type[/bold green]",
            choices=["coding", "writing", "image", "data analysis", "general"],
            default=target_type,
        )
        tone = Prompt.ask(
            "[bold green]Select Preferred Tone[/bold green]",
            choices=["concise", "detailed", "step-by-step", "expert"],
            default=tone,
        )

    try:
        result: OptimizerResult = optimize(
            prompt=input_prompt,
            target_type=target_type,
            tone=tone,
        )

        _render_summary(console, result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Optimization session cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Optimization Failed:[/bold red] {str(e)}")
        sys.exit(1)


def _render_summary(console: Console, result: OptimizerResult) -> None:
    """Render structured final output with Rich formatting."""
    console.print("\n")
    console.print(
        Panel(
            Syntax(result.optimized_prompt, "markdown", word_wrap=True),
            title="✨ Final Optimized Prompt ✨",
            border_style="bold green",
        )
    )

    # Score breakdown table
    score_table = Table(title="📊 Quality Scores Breakdown (Scale 0 - 10)")
    score_table.add_column("Metric", style="cyan", no_wrap=True)
    score_table.add_column("Score", style="bold yellow")

    s = result.score
    score_table.add_row("Overall Quality", f"{s.overall:.1f} / 10")
    score_table.add_row("Clarity", f"{s.clarity:.1f} / 10")
    score_table.add_row("Specificity", f"{s.specificity:.1f} / 10")
    score_table.add_row("Context Depth", f"{s.context:.1f} / 10")
    score_table.add_row("Constraints", f"{s.constraints:.1f} / 10")
    score_table.add_row("Output Format", f"{s.output_format:.1f} / 10")
    console.print(score_table)

    # Issues Identified
    if result.issues:
        console.print(Panel(
            "\n".join(f"• {issue}" for issue in result.issues),
            title="⚠️ Identified Weaknesses / Issues",
            border_style="yellow",
        ))

    # Actionable Tips
    if result.tips:
        console.print(Panel(
            "\n".join(f"💡 {tip}" for tip in result.tips),
            title="💡 Actionable Prompt Engineering Tips",
            border_style="blue",
        ))

    # Suggestions
    if result.suggestions:
        console.print(Panel(
            "\n".join(f"📌 {suggestion}" for suggestion in result.suggestions),
            title="📌 Further Suggestions & Edge Cases",
            border_style="magenta",
        ))

    # Follow up Questions
    if result.follow_up_questions:
        console.print(Panel(
            "\n".join(f"❓ {q}" for q in result.follow_up_questions),
            title="❓ Optional Follow-Up Questions",
            border_style="dim cyan",
        ))


if __name__ == "__main__":
    main()
