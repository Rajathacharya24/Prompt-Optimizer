# Setup Guide for Prompt-Optimizer

This guide explains how to set up the project on a new device and run it locally.

## 1. Prerequisites

Make sure your device has:

- Python 3.10 or newer
- pip (Python package installer)
- Git
- A terminal or command prompt

## 2. Clone the project

On Linux/macOS:

```bash
git clone https://github.com/Rajathacharya24/Prompt-Optimizer.git
cd Prompt-Optimizer
```

On Windows PowerShell:

```powershell
git clone https://github.com/Rajathacharya24/Prompt-Optimizer.git
cd Prompt-Optimizer
```

## 3. Create a virtual environment (recommended)

On Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```bash
cd prompt-optimizer-agent
pip install -r requirements.txt
```

## 5. Set environment variables

On Linux/macOS, set variables in the current shell:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_API_KEY="your-google-key"
export MODEL_NAME="claude-3-5-sonnet-20241022"
```

To make them persist for future shell sessions, add them to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

On Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

Optional providers:

```bash
export OPENAI_API_KEY="your-openai-key"
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_API_KEY="your-google-key"
export MODEL_NAME="claude-3-5-sonnet-20241022"
```

## 6. Run the project on Linux

### Activate the virtual environment

```bash
source .venv/bin/activate
```

### Interactive CLI

```bash
cd prompt-optimizer-agent
python -m agent.cli
```

### Direct prompt optimization

```bash
cd prompt-optimizer-agent
python -m agent.cli "Write a python script to parse CSV files" --type coding --tone detailed
```

## 7. Run tests on Linux

From the project root:

```bash
cd /home/rajathacharya/BroFFF/Prompt-Optimizer
pytest -q
```

Or from the package folder:

```bash
cd prompt-optimizer-agent
PYTHONPATH=. pytest
```

## 8. Troubleshooting

### Import errors

If Python cannot find the `agent` module, run tests from the project root or set the Python path:

```bash
PYTHONPATH=. pytest
```

### Missing packages

```bash
pip install -r requirements.txt
```

### API key errors

Make sure your selected provider key is exported before running the application.

## 9. Project structure

```text
Prompt-Optimizer/
├── README.md
├── PLAN.md
├── SETUP.md
├── pytest.ini
├── conftest.py
└── prompt-optimizer-agent/
    ├── agent/
    ├── tests/
    └── requirements.txt
```

## 10. Next step

After setup, you can start using the optimizer by running the CLI and entering your rough prompt.
