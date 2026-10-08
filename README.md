# Prompt-Optimizer

An autonomous, tool-augmented LLM agent that iteratively optimizes raw prompts into precise, structured, high-performing AI prompts.

For complete architectural details, component breakdowns, operational limits, and feature roadmaps, see [PLAN.md](file:///home/rajathacharya/BroFFF/Prompt-Optimizer/PLAN.md).

## Features

- **Standardized Prompt Structure**: Converts rough prompts into structured formats containing **Role**, **Context**, **Task**, **Constraints**, **Output Format**, and **Examples**.
- **Iterative Tool Loop**: Leverages LLM tool use (`analyze_prompt`, `test_prompt`, `ask_user`, `finalize`) to refine and test prompt candidates.
- **Rich Terminal UI**: Powered by `rich` to show step-by-step thinking, score breakdown tables, weakness identification, and actionable engineering tips.
- **Safety & Rate Limits**: Hard limits on step counts (max 8), draft rounds (max 3), user questions (max 2), and session execution timeouts (90s).

## Directory Structure

```text
Prompt-Optimizer/
├── PLAN.md                     # Architecture, design & development plan
├── README.md                   # Quickstart guide & documentation
└── prompt-optimizer-agent/     # Agent package source code
    ├── agent/                  # Optimization engine & CLI
    └── tests/                  # Pytest test suite
```

## Quick Start

### 1. Environment Setup

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 2. Run via CLI

```bash
cd prompt-optimizer-agent

# Interactive CLI mode
python -m agent.cli

# Direct prompt optimization
python -m agent.cli "Write a python script to parse CSV files" --type coding --tone detailed
```

### 3. Run Unit Tests

```bash
cd prompt-optimizer-agent
PYTHONPATH=. pytest
```