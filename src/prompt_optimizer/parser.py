from __future__ import annotations

import re
from typing import Iterable

from .schemas import StructuredIdea

_FIELD_ALIASES = {
    "goal": "goal",
    "objective": "goal",
    "audience": "audience",
    "constraints": "constraints",
    "constraint": "constraints",
    "output": "output_format",
    "output format": "output_format",
    "tone": "tone",
    "must include": "must_include",
    "include": "must_include",
    "problem": "problem_statement",
}


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def _split_items(value: str) -> list[str]:
    raw_items = re.split(r"\s*[;,]\s*|\s*\n\s*[-*]\s*", value.strip())
    return [item.strip(" -") for item in raw_items if item.strip(" -")]


def _extract_labeled_fields(lines: Iterable[str]) -> dict[str, str]:
    captured: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lower()
        key = _FIELD_ALIASES.get(key, "")
        if not key:
            continue
        captured[key] = right.strip()
    return captured


def _extract_inline_labeled_fields(text: str) -> dict[str, str]:
    captured: dict[str, str] = {}
    label_patterns = [
        r"goal",
        r"objective",
        r"audience",
        r"constraints?",
        r"output(?: format)?",
        r"tone",
        r"must include",
        r"include",
        r"problem",
    ]
    pattern = re.compile(
        rf"(?i)(?P<label>{'|'.join(label_patterns)})\s*:\s*(?P<value>.*?)"
        rf"(?=(?:\s+(?:{'|'.join(label_patterns)})\s*:)|$)"
    )
    for match in pattern.finditer(text):
        raw_label = match.group("label").strip().lower()
        normalized_label = _FIELD_ALIASES.get(raw_label, "")
        if not normalized_label:
            continue
        captured[normalized_label] = match.group("value").strip()
    return captured


def _infer_problem_statement(text: str) -> str:
    sentence_split = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentence_split:
        s = sentence.strip()
        if len(s) >= 25:
            return s
    return text[:160].strip() or "Define a clear, useful outcome from the raw idea."


def _infer_constraints(text: str) -> list[str]:
    constraints: list[str] = []
    lowered = text.lower()
    if "max" in lowered or "limit" in lowered:
        constraints.append("Respect any length or scope limits implied by the idea")
    if "deadline" in lowered or "by " in lowered:
        constraints.append("Address timeline expectations")
    if "no " in lowered or "avoid" in lowered:
        constraints.append("Avoid restricted content or style")
    return constraints


def parse_raw_idea(raw_text: str) -> StructuredIdea:
    text = _normalize(raw_text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    labeled = _extract_labeled_fields(lines)
    inline_labeled = _extract_inline_labeled_fields(text)
    for key, value in inline_labeled.items():
        if key not in labeled:
            labeled[key] = value

    problem_statement = labeled.get("problem_statement") or _infer_problem_statement(text)
    goal = labeled.get("goal") or "Produce a well-structured prompt from the raw idea"
    audience = labeled.get("audience") or "General professional audience"
    output_format = labeled.get("output_format") or "Structured response with clear sections"
    tone = labeled.get("tone") or "Direct and practical"

    constraints = _split_items(labeled["constraints"]) if "constraints" in labeled else _infer_constraints(text)
    must_include = _split_items(labeled["must_include"]) if "must_include" in labeled else []

    assumptions = [
        "The raw idea reflects the desired business or product context",
        "The user values clarity over verbosity",
    ]
    risks = [
        "Missing context may reduce precision",
        "Ambiguous goals can lead to generic output",
    ]

    return StructuredIdea(
        problem_statement=problem_statement,
        goal=goal,
        audience=audience,
        constraints=constraints,
        output_format=output_format,
        tone=tone,
        must_include=must_include,
        assumptions=assumptions,
        risks=risks,
    )
