from pathlib import Path

import pytest

from prompt_optimizer import diary
from prompt_optimizer.workflow import optimize_raw_idea


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "logs"
    monkeypatch.setattr(diary, "_DATA_DIR", path)
    return path


def test_auto_log_marks_day(data_dir):
    result = optimize_raw_idea("Goal: test logging; Output: short")
    entry = diary.log_session(result)

    assert entry["date"] is not None
    assert (data_dir / "daily_log.jsonl").exists()
    assert (data_dir / "daily_log.md").exists()
    md = (data_dir / "daily_log.md").read_text(encoding="utf-8")
    assert "## " in md and f"score: {entry['score']}" in md


def test_manual_log_marks_work(data_dir):
    diary.log_manual("built login page", "2 hrs")

    s = diary.stats()
    assert s["manual_today"] == 1
    assert s["minutes_today"] == 120
    md = diary.render_markdown()
    assert "built login page" in md and "2 hrs" in md


def test_streak_counts_consecutive_days(data_dir, monkeypatch):
    import json
    from datetime import date, timedelta

    logs = data_dir
    logs.mkdir(parents=True, exist_ok=True)
    today = date.today()
    rows = []
    for offset in (0, 1, 3):
        day = (today - timedelta(days=offset)).isoformat()
        rows.append({"date": day, "kind": "manual", "what": "x", "amount": "", "minutes": 0,
                     "word_count": 0, "score": 0, "task_type": "work-log", "time": "10:00"})
    (logs / "daily_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    # today + yesterday = streak of 2; day-3 gap breaks the chain
    assert diary.stats()["streak_days"] == 2


def test_empty_state(data_dir):
    assert diary.stats()["total_entries"] == 0
    assert diary.render_markdown().startswith("# Daily Log")


def test_full_flow_logs_into_diary(data_dir):
    result = optimize_raw_idea("Build a cli todo app in python, 200 lines max")
    diary.log_session(result)
    diary.log_manual("wrote tests", "45 min")

    s = diary.stats()
    assert s["sessions_today"] == 1
    assert s["manual_today"] == 1
    assert s["minutes_today"] == 45
    md = diary.render_markdown()
    assert "streak: 1 day(s)" in md
