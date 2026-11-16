from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

MD_NAME = "daily_log.md"
JSONL_NAME = "daily_log.jsonl"

_DATA_DIR: Path | None = None


def _data_dir() -> Path:
    return _DATA_DIR or Path.cwd() / "logs"


def set_data_dir(path: Path) -> None:
    global _DATA_DIR
    _DATA_DIR = path


def _jsonl_path() -> Path:
    return _data_dir() / JSONL_NAME


def _md_path() -> Path:
    return _data_dir() / MD_NAME


def _load_entries() -> list[dict]:
    path = _jsonl_path()
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _append_entry(entry: dict) -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    with _jsonl_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_session(result) -> dict:
    """Auto-log an optimization run. Marks what was done and how much."""
    analysis = result.analysis
    idea = result.structured_idea
    now = datetime.now()
    entry = {
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "kind": "auto",
        "task_type": analysis.task_type if analysis else "general",
        "word_count": analysis.word_count if analysis else len(str(result.optimized_prompt).split()),
        "score": analysis.overall_score if analysis else 0,
        "minutes": 0,
        "what": idea.goal[:120],
    }
    _append_entry(entry)
    _write_markdown()
    return entry


def log_manual(what: str, amount: str) -> dict:
    """Log a manual work entry: what you did + how much."""
    what = (what or "").strip() or "Untitled task"
    amount = (amount or "").strip()
    now = datetime.now()
    minutes = 0
    m = None
    import re

    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hours?|m|min|mins|minutes?)\b", amount, re.I):
        value, unit = float(m.group(1)), m.group(2).lower()
        minutes += int(value * 60 if unit.startswith("h") else value)
    entry = {
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "kind": "manual",
        "task_type": "work-log",
        "what": what[:160],
        "amount": amount[:80],
        "minutes": minutes,
        "word_count": 0,
        "score": 0,
    }
    _append_entry(entry)
    _write_markdown()
    return entry


def entries_on(day: str) -> list[dict]:
    return [e for e in _load_entries() if e.get("date") == day]


def _streak(today: date) -> int:
    days = {e.get("date") for e in _load_entries()}
    streak = 0
    cursor = today
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def stats() -> dict:
    entries = _load_entries()
    today = date.today().isoformat()
    todays = [e for e in entries if e.get("date") == today]
    scored = [e for e in entries if e.get("kind") == "auto"]
    scores = [e["score"] for e in scored if e.get("score")]
    return {
        "date": today,
        "sessions_today": len([e for e in todays if e.get("kind") == "auto"]),
        "manual_today": len([e for e in todays if e.get("kind") == "manual"]),
        "minutes_today": sum(e.get("minutes", 0) for e in todays),
        "words_processed_today": sum(e.get("word_count", 0) for e in todays),
        "total_entries": len(entries),
        "avg_score": round(sum(scores) / len(scores)) if scores else 0,
        "streak_days": _streak(date.today()),
    }


def render_markdown() -> str:
    entries = _load_entries()
    by_day: dict[str, list[dict]] = {}
    for e in entries:
        by_day.setdefault(e.get("date", "unknown"), []).append(e)

    lines = ["# Daily Log", ""]
    for day in sorted(by_day, reverse=True):
        day_entries = by_day[day]
        minutes = sum(e.get("minutes", 0) for e in day_entries)
        words = sum(e.get("word_count", 0) for e in day_entries)
        auto = [e for e in day_entries if e.get("kind") == "auto"]
        scores = [e["score"] for e in auto if e.get("score")]
        lines.append(f"## {day}")
        lines.append("")
        for e in day_entries:
            if e.get("kind") == "manual":
                lines.append(f"- {e.get('time', '--:--')} | work-log | {e.get('what', '')} | {e.get('amount', '')}")
            else:
                idea_head = str(e.get("what", "")).replace("|", "/")
                lines.append(
                    f"- {e.get('time', '--:--')} | {e.get('task_type', 'general')} "
                    f"| words: {e.get('word_count', 0)} | score: {e.get('score', 0)} | {idea_head}"
                )
        avg = round(sum(scores) / len(scores)) if scores else 0
        lines.append("")
        lines.append(
            f"**day summary:** entries {len(day_entries)} · words {words} · minutes {minutes} · avg score {avg}"
        )
        lines.append("")

    s = stats()
    lines.append("---")
    lines.append(
        f"**today:** {s['sessions_today']} optimized · {s['manual_today']} manual · "
        f"{s['minutes_today']} min · **streak: {s['streak_days']} day(s)** · lifetime entries: {s['total_entries']}"
    )
    lines.append("")
    return "\n".join(lines)


def _write_markdown() -> None:
    _md_path().write_text(render_markdown(), encoding="utf-8")
