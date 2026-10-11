# Prompt-Optimizer

An autonomous, tool-augmented LLM agent that turns rough prompts into precise, structured, high-performing ones.

## Features

- **Structured output**: Rewrites prompts into a standard format: **Role, Context, Task, Constraints, Output Format, Examples**.
- **Iterative tool loop**: The agent refines candidates using `analyze_prompt`, `test_prompt`, `ask_user`, and `finalize`.
- **Rich terminal UI**: Built on `rich`, with step-by-step reasoning, score breakdown tables, identified weaknesses, and prompt-engineering tips.
- **Built-in limits**: Max 8 steps, 3 draft rounds, 2 user questions, and a 90s session timeout.

## Requirements

- Python 3.10+ (adjust to your actual minimum)
- An [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
git clone <repo-url>
cd Prompt-Optimizer/prompt-optimizer-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

**Interactive mode**

```bash
python -m agent.cli
```

**Direct optimization**

```bash
python -m agent.cli "Write a python script to parse CSV files" --type coding --tone detailed
```

| Option   | Description                          | Example values            |
|----------|--------------------------------------|---------------------------|
| `--type` | Category of the prompt's task        | `coding`, ...             |
| `--tone` | Desired style of the optimized prompt| `detailed`, ...           |

## Example

**Input:** `Write a python script to parse CSV files`

**Output:** *(paste a short before/after here, this is the most persuasive part of a README)*

## Testing

```bash
cd prompt-optimizer-agent
PYTHONPATH=. pytest
```

## Project Structure

```text
Prompt-Optimizer/
├── PLAN.md                     # Architecture, design, and roadmap
├── README.md
└── prompt-optimizer-agent/
    ├── agent/                  # Optimization engine and CLI
    └── tests/                  # Pytest suite
```

See [PLAN.md](PLAN.md) for architecture details, component breakdowns, operational limits, and the roadmap.

## License

*(Add a license, e.g. MIT.)*
