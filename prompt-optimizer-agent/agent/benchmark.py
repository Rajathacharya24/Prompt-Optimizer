"""Comparative benchmark runner evaluating raw vs. optimized prompt performance side-by-side."""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .adapters import BaseLLMAdapter, get_adapter
from .agent import optimize
from .schemas import OptimizerResult


def run_benchmark(
    prompt: str,
    provider: str = "anthropic",
    model_name: Optional[str] = None,
    target_type: str = "general",
    tone: str = "detailed",
    adapter: Optional[BaseLLMAdapter] = None,
) -> Dict[str, Any]:
    """Execute raw prompt vs optimized prompt comparison benchmark.

    Args:
        prompt: Initial raw user prompt string.
        provider: LLM provider name ('anthropic', 'openai', 'gemini', 'ollama', 'mock').
        model_name: Optional model identifier.
        target_type: Category of task domain.
        tone: Desired prompt tone.
        adapter: Optional custom adapter instance.

    Returns:
        Dict[str, Any]: Detailed comparison metrics payload.
    """
    console = Console()
    llm_adapter = adapter or get_adapter(provider=provider, model_name=model_name)

    console.print(
        Panel(
            f"[bold magenta]🚀 Starting Benchmark Evaluation[/bold magenta]\n"
            f"[bold yellow]Raw Prompt:[/bold yellow] {prompt}\n"
            f"[bold green]Provider:[/bold green] {llm_adapter.__class__.__name__} ({llm_adapter.model_name})",
            title="Prompt Optimizer Benchmark",
            border_style="magenta",
        )
    )

    # 1. Run optimization
    opt_start = time.time()
    result: OptimizerResult = optimize(
        prompt=prompt,
        target_type=target_type,
        tone=tone,
        adapter=llm_adapter,
    )
    opt_duration = time.time() - opt_start

    optimized_prompt = result.optimized_prompt

    # 2. Test Raw Prompt against LLM
    console.print("\n[bold cyan]⏳ Running Raw Prompt in LLM Sandbox...[/bold cyan]")
    raw_start = time.time()
    raw_output = llm_adapter.test_prompt(prompt=prompt, max_tokens=800)
    raw_latency = time.time() - raw_start

    # 3. Test Optimized Prompt against LLM
    console.print("[bold green]⏳ Running Optimized Prompt in LLM Sandbox...[/bold green]")
    opt_eval_start = time.time()
    opt_output = llm_adapter.test_prompt(prompt=optimized_prompt, max_tokens=800)
    opt_latency = time.time() - opt_eval_start

    # 4. Metric Extraction
    raw_metrics = _compute_output_metrics(raw_output, raw_latency)
    opt_metrics = _compute_output_metrics(opt_output, opt_latency)

    benchmark_data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "provider": llm_adapter.__class__.__name__,
        "model_name": llm_adapter.model_name,
        "raw_prompt": prompt,
        "optimized_prompt": optimized_prompt,
        "optimizer_result": result.model_dump(),
        "optimization_time_sec": round(opt_duration, 2),
        "raw_benchmark": raw_metrics,
        "optimized_benchmark": opt_metrics,
    }

    _render_benchmark_report(console, benchmark_data)
    _save_benchmark_run(benchmark_data)

    return benchmark_data


def _compute_output_metrics(text: str, latency: float) -> Dict[str, Any]:
    """Calculate quantitative structural metrics on generated text."""
    words = len(text.split())
    chars = len(text)
    headers = text.count("#")
    code_blocks = text.count("```") // 2
    bullet_points = text.count("- ") + text.count("* ")

    # Structural richness score heuristic (0 to 10)
    structure_score = min(
        10.0,
        (headers * 1.5) + (code_blocks * 2.0) + (1.0 if bullet_points > 0 else 0.0) + (3.0 if words > 50 else 1.0),
    )

    return {
        "output_text": text,
        "latency_sec": round(latency, 3),
        "word_count": words,
        "char_count": chars,
        "headers_count": headers,
        "code_blocks_count": code_blocks,
        "bullet_points_count": bullet_points,
        "structure_score": round(structure_score, 1),
    }


def _render_benchmark_report(console: Console, data: Dict[str, Any]) -> None:
    """Render comparative results using Rich side-by-side formatting."""
    console.print("\n")
    console.print(
        Panel(
            "[bold green]📊 Benchmark Evaluation Summary Report[/bold green]",
            border_style="bold magenta",
        )
    )

    table = Table(title="📈 Side-by-Side Performance Comparison")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Raw Prompt Output", style="bold yellow")
    table.add_column("Optimized Prompt Output", style="bold green")
    table.add_column("Improvement / Delta", style="bold magenta")

    raw = data["raw_benchmark"]
    opt = data["optimized_benchmark"]

    # Latency comparison
    table.add_row(
        "Response Latency",
        f"{raw['latency_sec']}s",
        f"{opt['latency_sec']}s",
        f"{opt['latency_sec'] - raw['latency_sec']:+.3f}s",
    )
    # Word count
    table.add_row(
        "Word Count",
        f"{raw['word_count']} words",
        f"{opt['word_count']} words",
        f"{opt['word_count'] - raw['word_count']:+d} words",
    )
    # Headers
    table.add_row(
        "Markdown Headers",
        str(raw["headers_count"]),
        str(opt["headers_count"]),
        f"{opt['headers_count'] - raw['headers_count']:+d}",
    )
    # Code Blocks
    table.add_row(
        "Code Blocks",
        str(raw["code_blocks_count"]),
        str(opt["code_blocks_count"]),
        f"{opt['code_blocks_count'] - raw['code_blocks_count']:+d}",
    )
    # Structure Score
    table.add_row(
        "Structure Score",
        f"{raw['structure_score']} / 10",
        f"{opt['structure_score']} / 10",
        f"{opt['structure_score'] - raw['structure_score']:+.1f}",
    )

    console.print(table)

    # Side-by-side outputs
    console.print("\n[bold yellow]--- Raw Prompt Output ---[/bold yellow]")
    console.print(Panel(Syntax(raw["output_text"], "markdown", word_wrap=True), border_style="yellow"))

    console.print("\n[bold green]--- Optimized Prompt Output ---[/bold green]")
    console.print(Panel(Syntax(opt["output_text"], "markdown", word_wrap=True), border_style="green"))


def _save_benchmark_run(data: Dict[str, Any]) -> str:
    """Save benchmark result object to runs/benchmark_<timestamp>.json."""
    base_dir = os.getcwd()
    runs_dir = os.path.join(base_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(runs_dir, f"benchmark_{timestamp}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filepath
