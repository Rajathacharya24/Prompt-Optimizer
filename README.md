# Prompt-Optimizer

An autonomous, tool-augmented LLM agent that turns rough prompts into precise, structured, high-performing instructions for AI systems.

## Features

- **Structured prompt rewriting**: Converts rough input into a consistent format with Role, Context, Task, Constraints, Output Format, and Examples.
- **Iterative optimization loop**: Uses `analyze_prompt`, `test_prompt`, `ask_user`, and `finalize` to improve candidate prompts over a bounded number of steps.
- **Rich terminal output**: Displays reasoning, tool calls, draft candidates, score breakdowns, weaknesses, and actionable prompt-engineering guidance.
- **Built-in safety limits**: Enforces a max of 8 LLM steps, 3 draft rounds, 2 clarification questions, and a 90-second session timeout.
- **Multi-provider support**: Works with Anthropic, OpenAI, Gemini, Ollama, and a mock adapter for local tests.

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/) for the default provider
- Optional: OpenAI, Gemini, or Ollama credentials depending on provider choice

## Installation

```bash
git clone https://github.com/Rajathacharya24/Prompt-Optimizer.git
cd Prompt-Optimizer/prompt-optimizer-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

### Interactive mode

```bash
python -m agent.cli
```

### Direct optimization

```bash
python -m agent.cli "Write a python script to parse CSV files" --type coding --tone detailed
```

### Supported options

| Option | Description | Example values |
| --- | --- | --- |
| `--type` | Target prompt category | `coding`, `writing`, `image`, `data analysis`, `general` |
| `--tone` | Desired writing style of the optimized prompt | `concise`, `detailed`, `step-by-step`, `expert` |
| `--provider` | LLM provider to use | `anthropic`, `openai`, `gemini`, `ollama`, `mock` |
| `--model` | Model name for the selected provider | `claude-3-5-sonnet-20241022`, `gpt-4o`, `llama3` |
| `--benchmark` | Run a raw-vs-optimized benchmark | `--benchmark` |

## Example

**Input**

```text
Write a python script to parse CSV files
```

**Optimized output**

```text
**Role**: Senior Python Developer

**Context**: You are building a utility script for data processing in a business workflow. The script must handle CSV files with headers, missing values, and large row counts efficiently.

**Task**: Write a Python script that reads a CSV file, validates the input structure, cleans malformed rows, and outputs a processed dataset or summary statistics.

**Constraints**:
- Use Python standard library only unless otherwise specified.
- Handle missing values and invalid rows without crashing.
- Keep the script readable, modular, and easy to maintain.
- Prefer clear function names and type hints.

**Output Format**:
- Provide a single code block containing the script.
- Add a short explanation of the design choices and assumptions.

**Examples**:
- Example input: `product_id,category,price\n1,books,19.99\n2,,5.00`
- Example output: a cleaned list of rows or a summary dictionary.
```

## Running Tests

```bash
cd prompt-optimizer-agent
PYTHONPATH=. pytest
```

## Project Structure

```text
Prompt-Optimizer/
├── LICENSE                     # MIT license
├── PLAN.md                    # Architecture, design, and roadmap
├── README.md                  # Project overview and usage guide
└── prompt-optimizer-agent/
    ├── agent/                 # Core optimization engine, adapters, CLI, schemas, tools
    └── tests/                 # Pytest suite covering the optimization loop and benchmark logic
```

See [PLAN.md](PLAN.md) for the full architecture, operational guardrails, and roadmap.

## License

This project is licensed under the [MIT License](LICENSE).
