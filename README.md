# Prompt Optimizer

A small, local tool that turns a raw, messy idea into a clear, structured,
production-ready prompt for an AI model.

It does **not** call any AI service and needs no API key or internet. It is pure
Python: it reads your idea, finds what is missing, and builds a better prompt
that you can copy into ChatGPT, Claude, or any other AI tool.

## What problem does it solve?

Most people give AI short, vague instructions like "write something about our
new app". The AI then guesses, and the result is generic, off-target, or missing
the point. Writing a really good prompt by hand is slow, and it is easy to
forget important parts such as the audience, the output format, or the limits.

Prompt Optimizer fixes that by:

- **Filling in the gaps** – it detects missing details (audience, tone, output
  format, constraints) and either asks you about them or makes a sensible,
  clearly stated assumption.
- **Adding structure** – it wraps your idea in a proven prompt shape (role,
  context, objective, steps, quality bar) so the AI knows exactly what to do.
- **Making quality visible** – it scores your idea on clarity, specificity and
  completeness, and tells you what to add to improve it.
- **Keeping a record** – every run is logged so you can see what you worked on,
  your average score, and your daily streak.

## What does it do? (how it works)

```
Raw idea → Parse & analyze → Interview (fill gaps) → Build blueprint → Render optimized prompt → Log it
```

1. **Parse** – reads free text, or labeled lines such as `Goal:`, `Audience:`,
   `Constraints:`, `Output:`, `Tone:`, `Must Include:`. It also infers the task
   type (code, analysis, writing, marketing, planning, learning, design, or
   general) and picks an expert role to match.
2. **Analyze** – scores clarity, specificity and completeness from 0–100 and
   suggests concrete improvements (for example "Add an 'audience' line").
3. **Interview** (web UI) – if details are missing, it asks a few quick
   multiple-choice questions, then applies your answers and re-scores the idea.
4. **Plan** – builds a blueprint: task steps, a quality bar, and a fixed output
   schema, all tailored to the detected task type.
5. **Render** – produces the final prompt with clear sections: ROLE, CONTEXT,
   OBJECTIVE, CONSTRAINTS, MUST INCLUDE, PROCESS, OUTPUT FORMAT, QUALITY BAR and
   TONE. It ends with an instruction to commit to an answer instead of hedging.
6. **Log** – saves the run to `logs/daily_log.md` and `logs/daily_log.jsonl`
   with stats (runs today, words processed, average score, streak).

## How do we use it?

### Install

```bash
pip install -e .
```

### 1. Terminal-style web UI (recommended)

```bash
python -m prompt_optimizer.web          # or: prompt-optimizer-web
```

Open http://127.0.0.1:7860 — a black/grey/yellow terminal UI. Paste your raw
idea and press Enter. It asks a few short questions, then shows the optimized
prompt with live analysis (task type, clarity, specificity, completeness) and
improvement suggestions.

- `↑` / `↓` – recall history
- `Shift+Enter` – add a newline
- `[copy]` – copy the result
- `/log what you did | 2 hrs` – log manual work
- `/today` (or the `[ log ]` button) – view the daily log and streak

Optional flags: `--host 0.0.0.0 --port 8000`

### 2. CLI

```bash
prompt-optimizer optimize --idea "Goal: Explain our API migration plan to enterprise customers. Constraints: concise. Output: bullet list."
```

Read from a file:

```bash
prompt-optimizer optimize --file idea.txt
```

Add `--json` for machine-readable output (includes the analysis scores).

### 3. API

Start the server with `python -m prompt_optimizer.web`, then call:

```bash
curl -X POST http://127.0.0.1:7860/api/prompt-optimizer \
  -H 'Content-Type: application/json' \
  -d '{"idea":"Goal: Build a launch email. Audience: Founders. Constraints: 120 words max. Output: Subject + body."}'
```

Response JSON fields:

- `formatted` – display text with `**Optimized Prompt:**` (fenced block),
  `**Assumptions:**`, and optional `**Quick questions (optional):**`
- `optimized_prompt` – the prompt text inside the fence
- `assumptions` – assumptions that were made
- `quick_questions` – questions returned when the idea is too vague
- `vague` – true when questions were returned instead of a prompt
- `text` – same as `formatted`

The body also accepts `rawIdea` as the input key. Empty input returns HTTP 400.

Other endpoints:

- `POST /api/optimize` – full structured result (idea, blueprint, prompt,
  analysis) and auto-logs the run
- `POST /api/interview/start` and `/api/interview/finish` – the question flow
  used by the web UI
- `GET /api/log` and `POST /api/log` – read or add daily-log entries

## What does a good input look like?

Free text works, but the parser works best when you include labels like:

- **Goal** – what outcome is needed
- **Audience** – who this is for
- **Constraints** – limits, rules, deadlines
- **Output** – required output format
- **Tone** – writing style
- **Must Include** – mandatory points

```text
Goal: Build a launch email for a new AI note-taking app
Audience: Startup founders
Constraints: 120 words max, no hype language
Output: Subject line + body
Tone: Clear and practical
Must Include: Product value, one CTA, free trial mention
```

The more of these you provide, the higher the completeness score and the less
the tool has to guess.

## Engine (v1.0)

1. **Parser** – extracts labeled fields, infers the rest, and detects task type.
2. **Analyzer** – scores clarity, specificity and completeness (0–100) and emits
   suggestions for raising the score.
3. **Planner** – task-type-aware process steps, quality bar, output schema and
   an expert role per domain.
4. **Renderer** – emits a structured prompt (ROLE / CONTEXT / OBJECTIVE /
   CONSTRAINTS / MUST INCLUDE / PROCESS / OUTPUT FORMAT / QUALITY BAR / TONE),
   closed with an anti-hedging instruction so the model commits to an answer.
