from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import optimize_raw_idea


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prompt-optimizer",
        description="Convert a raw idea into a structured optimized prompt",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    optimize_cmd = subparsers.add_parser("optimize", help="Run full optimization flow")
    optimize_cmd.add_argument("--idea", type=str, help="Raw idea text")
    optimize_cmd.add_argument("--file", type=Path, help="Path to text file containing idea")
    optimize_cmd.add_argument("--json", action="store_true", help="Output JSON")

    return parser


def _read_raw_idea(idea: str | None, file_path: Path | None) -> str:
    if idea:
        return idea
    if file_path:
        return file_path.read_text(encoding="utf-8")
    return input("Paste your raw idea: ").strip()


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "optimize":
        parser.error("Unknown command")

    raw_idea = _read_raw_idea(args.idea, args.file)
    result = optimize_raw_idea(raw_idea)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("Structured Idea")
    print(json.dumps(result.structured_idea.to_dict(), indent=2))
    print("\nOptimized Prompt\n")
    print(result.optimized_prompt)


if __name__ == "__main__":
    main()
