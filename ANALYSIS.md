# Prompt-Optimizer — Project Analysis & Roadmap

> Analysis date: 2026-11-12 · Status: ~85–90% complete (CLI + agent loop done, web dashboard pending)

---

## 1. What This Project Is (Intent)

**Prompt-Optimizer is an autonomous LLM agent that transforms rough, vague prompts (e.g. "Build API") into precise, structured prompts** using a standard format:

**Role / Context / Task / Constraints / Output Format / Examples**

Core goals:
- Preserve the user's original intent while improving clarity, specificity, and structure
- Run a closed-loop cycle: **analyze → draft → test → critique → revise → finalize**
- *Prove* the improvement by benchmarking raw vs optimized prompt outputs
- Enforce deterministic guardrails so the agent can never loop forever

---

## 2. Full Flow (End-to-End)

```
User prompt
    │
    ▼
CLI entry ──► agent/cli.py:16 (main)          ← interactive mode if no prompt given
    │         args: --type, --tone, --provider, --model, --benchmark
    ▼
optimize() ──► agent/agent.py:36              ← THE AGENT LOOP (max 8 steps / 90s)
    │
    │   1. Build system prompt (agent/system_prompt.py:56)
    │   2. Send prompt + 4 tools to the LLM
    │
    ▼   LLM calls tools in a loop:
    │
    ├─ analyze_prompt ──► tools.py:78   deterministic "diagnosis" (no LLM)
    ├─ ask_user        ──► tools.py:159 clarifying questions (max 2)
    ├─ test_prompt     ──► tools.py:123 sandbox-runs the draft (max 3 rounds)
    └─ finalize        ──► agent.py:236  Pydantic-validated final result
    │
    ▼
Early exit if self-score ≥ 8.0  (agent.py:291)
    │
    ▼
Rich-rendered summary (cli.py:126): optimized prompt, score table, issues, tips
    │
    ▼
Saved to runs/<timestamp>.json  (agent.py:20)
    │
    ▼  (optional --benchmark)
run_benchmark() (benchmark.py:19): runs RAW vs OPTIMIZED prompt side-by-side,
compares latency / word count / headers / code blocks / structure_score
```

### Project structure

```
Prompt-Optimizer/
├── README.md, PLAN.md, SETUP.md, LICENSE
├── pyproject.toml, pytest.ini, conftest.py, sitecustomize.py
├── runs/                          # 10 optimization runs + 5 benchmark runs (JSON)
└── prompt-optimizer-agent/
    ├── requirements.txt
    ├── agent/
    │   ├── agent.py               # Main optimization loop
    │   ├── adapters.py            # Multi-provider LLM adapters (493 lines)
    │   ├── tools.py               # Tool definitions, implementations, dispatcher
    │   ├── benchmark.py           # Raw-vs-optimized comparison runner
    │   ├── cli.py                 # CLI entry point
    │   ├── schemas.py             # Pydantic models (Score, OptimizerResult, Event)
    │   ├── system_prompt.py       # Prompt-engineering system prompt
    │   └── __init__.py
    └── tests/                     # test_loop.py, test_adapters.py, test_benchmark.py
```

---

## 3. What Is "Diagnosed" (3 Evaluation Layers)

### A. Structural diagnosis — `execute_analyze_prompt()` (tools.py:78)
Pure Python heuristics, no LLM call:
- **Intent classification** by keywords → coding / writing / image / data analysis / general
- **Missing-info detection**: no role/persona, too brief (<12 words), no output format, no constraints
- **Flags**: `has_role`, `has_constraints`, `has_output_format`, `word_count`

### B. LLM self-assessment — `Score` (schemas.py:8)
The model scores its final prompt 0.0–10.0 on six dimensions:
`overall, clarity, specificity, context, constraints, output_format`
- Enforced by Pydantic (`Field(ge=0.0, le=10.0)`)
- **overall ≥ 8.0 triggers early stop** (agent.py:291)

### C. Quantitative benchmark — `benchmark.py`
- Runs both the raw and the optimized prompt in an LLM sandbox (800 tokens each)
- `_compute_output_metrics()` (benchmark.py:99): word count, char count, `#` headers, code blocks, bullets → **structure_score 0–10**
- Side-by-side Rich comparison table; saved as `runs/benchmark_<timestamp>.json`

Finalize also outputs: `issues`, `tips` (3–6), `suggestions`, `follow_up_questions`.

---

## 4. Guardrails

| Constraint | Limit | Location |
|---|---|---|
| Max LLM steps | 8 (forced finalize at 8) | agent.py:116, 128 |
| Session timeout | 90 seconds | agent.py:119 |
| Clarifying questions | max 2 | agent.py:190 |
| Draft/test rounds | max 3 | agent.py:225 |
| Early stop | score ≥ 8.0 | agent.py:291 |
| Schema-validation retry | exactly 1 | agent.py:240 |

---

## 5. Providers & Adapters (agent/adapters.py)

| Adapter | Default model | Tool calling | Notes |
|---|---|---|---|
| `AnthropicAdapter` | `claude-3-5-sonnet-20241022` | ✅ native | Default provider |
| `OpenAIAdapter` | `gpt-4o` | ✅ converted format | |
| `GeminiAdapter` | `gemini-1.5-pro` | ❌ text only | Agent loop can't drive tools |
| `OllamaAdapter` | `llama3` | ⚠️ depends on model | Local, `localhost:11434` |
| `MockAdapter` | `mock-model` | ✅ scripted | Offline/testing fallback |

`get_adapter()` (adapters.py:456): resolves provider from `--provider` or `MODEL_PROVIDER` env; **no key → auto-falls back to mock** so everything works offline.

---

## 6. Setup (Quick Start)

```bash
cd Prompt-Optimizer/prompt-optimizer-agent
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-..."    # required for real runs (default provider)
# Optional: OPENAI_API_KEY / GEMINI_API_KEY / OLLAMA_BASE_URL
# Optional: MODEL_PROVIDER=anthropic|openai|gemini|ollama|mock

python -m agent.cli                                   # interactive mode
python -m agent.cli "write a blog" --type writing --tone detailed
python -m agent.cli "Build API" --benchmark           # raw-vs-optimized comparison

pytest -q                                             # run tests (from repo root, all mocked)
```

Results are saved automatically to `runs/<YYYYmmdd_HHMMSS>.json`.

---

## 7. What You Should Do Next (Roadmap)

### Immediate / High priority
1. **Do a real (non-mock) end-to-end test** — all existing `runs/` artifacts are mock-adapter runs. Set `ANTHROPIC_API_KEY` and run one real optimization + one `--benchmark` to validate actual behavior.
2. **Fix or gate the Gemini adapter** — it has no tool calling (tools.py loop can't drive it; it will keep getting nudged to call tools). Either add Gemini function-calling support or raise a clear error / disable the agent loop for Gemini.
3. **Clean up stale references** — SETUP.md line 114 points to an old path (`/home/rajathacharya/BroFFF/Prompt-Optimizer`); git commit messages contain typos ("Updated Usused files").

### Short term
4. **Build Phase 3: FastAPI web dashboard/API** (planned in PLAN.md, not started):
   - `POST /optimize` endpoint wrapping `optimize()`
   - Stream agent `Event`s (already defined in schemas.py:39–57) via SSE/WebSocket
   - Simple UI to submit prompts and view results/benchmarks
5. **Real-prompt test suite** — add a set of standard "before" prompts (like `"Build API"`, `"write essay"`) and assert the optimized output passes structural checks (has role, format, constraints).
6. **Strengthen benchmark scoring** — current `structure_score` is a rough heuristic; consider adding an LLM-as-judge comparison or pairwise preference check.

### Later / nice-to-have
7. **Token/cost tracking** — log tokens and estimated cost per run into the saved JSON.
8. **Config file support** — a `config.yaml`/`.toml` for default provider, model, tone, limits (currently env vars + CLI flags only).
9. **Retry/resume for the 90s timeout** — currently a timeout kills the run; consider checkpointing message history.
10. **CI** — GitHub Actions running `pytest -q` on push.

---

## 8. Key Files Quick Reference

| Item | Location | Role |
|---|---|---|
| `optimize()` | agent/agent.py:36 | Main agent loop |
| `_save_run()` | agent/agent.py:20 | Persists result to `runs/` |
| `TOOLS_DEFINITIONS` | agent/tools.py:6 | Anthropic-style tool schemas |
| `execute_analyze_prompt()` | agent/tools.py:78 | Structural diagnosis |
| `execute_test_prompt()` | agent/tools.py:123 | LLM sandbox test |
| `execute_ask_user()` | agent/tools.py:159 | Clarification |
| `dispatch_tool_call()` | agent/tools.py:168 | Safe central dispatcher |
| `get_system_prompt()` | agent/system_prompt.py:56 | System prompt builder |
| `Score` | agent/schemas.py:8 | 6-dimension score model |
| `OptimizerResult` | agent/schemas.py:19 | Final validated payload |
| `Event` / `EventType` | agent/schemas.py:39 | Streaming event model |
| `BaseLLMAdapter` | agent/adapters.py:27 | Abstract adapter ABC |
| `get_adapter()` | agent/adapters.py:456 | Provider factory |
| `main()` | agent/cli.py:16 | CLI entry point |
| `_render_summary()` | agent/cli.py:126 | Rich final rendering |
| `run_benchmark()` | agent/benchmark.py:19 | Raw-vs-optimized comparison |
