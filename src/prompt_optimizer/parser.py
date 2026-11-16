from __future__ import annotations

import re

from .schemas import PromptAnalysis, StructuredIdea

_FIELD_ALIASES = {
    "goal": "goal",
    "objective": "goal",
    "task": "goal",
    "audience": "audience",
    "constraints": "constraints",
    "constraint": "constraints",
    "output": "output_format",
    "output format": "output_format",
    "format": "output_format",
    "tone": "tone",
    "must include": "must_include",
    "include": "must_include",
    "problem": "problem_statement",
}

# Ordered by priority: first match wins.
_TASK_TYPES = [
    ("code", [
        "code", "app", "application", "website", "web", "api", "script",
        "function", "bug", "debug", "refactor", "program", "software",
        "database", "frontend", "backend", "fullstack", "deploy", "feature",
    ]),
    ("analysis", [
        "analyze", "analysis", "research", "compare", "evaluate", "review",
        "audit", "report", "data", "insight", "investigate", "assess", "study",
    ]),
    ("writing", [
        "write", "draft", "blog", "article", "essay", "copy", "story",
        "newsletter", "email copy", "caption", "script for video", "content",
    ]),
    ("marketing", [
        "marketing", "campaign", "ad", "advert", "seo", "brand", "launch",
        "social media", "post", "growth", "landing page copy", "sales",
    ]),
    ("planning", [
        "plan", "roadmap", "strategy", "schedule", "organize", "manage",
        "workflow", "process", "timeline", "checklist", "itinerary",
    ]),
    ("learning", [
        "explain", "teach", "learn", "tutorial", "guide", "how to",
        "beginner", "study plan", "course", "lesson",
    ]),
    ("design", [
        "design", "ui", "ux", "logo", "wireframe", "mockup", "layout",
        "prototype", "user flow",
    ]),
]

_ROLE_BY_TYPE = {
    "code": "senior software engineer",
    "analysis": "senior analyst",
    "writing": "professional writer",
    "marketing": "growth marketing strategist",
    "planning": "seasoned project strategist",
    "learning": "expert educator",
    "design": "product designer",
    "general": "domain expert consultant",
}

_VAGUE_WORDS = {"good", "nice", "great", "better", "stuff", "things", "etc", "something", "somehow", "best"}


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def _split_items(value: str) -> list[str]:
    raw_items = re.split(r"\s*[;,]\s*|\s*\n\s*[-*]\s*", value.strip())
    return [item.strip(" -") for item in raw_items if item.strip(" -")]


def _extract_labeled_fields(lines) -> dict[str, str]:
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
        "must include",
        "output format",
        "output",
        "format",
        "constraints?",
        "constraint",
        "objective",
        "problem",
        "audience",
        "task",
        "goal",
        "tone",
        "include",
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


def _detect_task_type(text: str) -> tuple[str, list[str]]:
    lowered = text.lower()
    best_type, best_hits = "general", []
    for task_type, keywords in _TASK_TYPES:
        hits = [kw for kw in keywords if kw in lowered]
        if len(hits) > len(best_hits):
            best_type, best_hits = task_type, hits
    return best_type, best_hits


def _infer_problem_statement(text: str) -> str:
    sentence_split = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentence_split:
        s = sentence.strip()
        if len(s) >= 25:
            return s.rstrip(".!?")
    return text[:160].strip().rstrip(".!?") or "Define a clear, useful outcome from the raw idea."


def _infer_constraints(text: str) -> list[str]:
    inferred: list[str] = []
    lowered = text.lower()
    number_match = re.search(r"\b(\d+)\s*(words|characters|chars|paragraphs|items|bullets|slides|pages|lines)\b", lowered)
    if number_match:
        inferred.append(f"Strict limit: {number_match.group(0).strip()}")
    if "max" in lowered or "limit" in lowered or number_match:
        inferred.append("Respect any length or scope limits implied by the idea")
    if "deadline" in lowered or "by " in lowered or "days" in lowered or "week" in lowered:
        inferred.append("Address timeline expectations where relevant")
    if re.search(r"\bno \w+|\bavoid\w*\b|\bdon't\b|\bwithout\b", lowered):
        inferred.append("Avoid the content, style, or approach the idea explicitly rules out")
    if not inferred:
        inferred.append("Stay within the scope implied by the idea; do not invent extra requirements")
    return inferred


def _strip_trailing_punct(value: str) -> str:
    return value.strip().rstrip(".!?")


def parse_raw_idea(raw_text: str, *, with_analysis: bool = False):
    text = _normalize(raw_text)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    labeled = _extract_labeled_fields(lines)
    inline_labeled = _extract_inline_labeled_fields(text)
    labeled.update(inline_labeled)
    explicit_fields = set(labeled.keys())

    task_type, signals = _detect_task_type(text)

    problem_statement = labeled.get("problem_statement") or _infer_problem_statement(text)
    goal = _strip_trailing_punct(labeled.get("goal") or text)
    if len(goal) > 180:
        goal = goal[:180].strip()
    audience = _strip_trailing_punct(labeled.get("audience") or "")
    if not audience:
        audience = "Technical peers" if task_type == "code" else "General professional audience"
    output_format = _strip_trailing_punct(labeled.get("output_format") or "") or "Structured response with clear headed sections"
    tone = _strip_trailing_punct(labeled.get("tone") or "") or "Direct, practical, and confident"

    constraints = _split_items(labeled["constraints"]) if "constraints" in labeled else _infer_constraints(text)
    must_include = _split_items(labeled["must_include"]) if "must_include" in labeled else []
    if not must_include:
        must_include = ["Concrete, immediately usable content (no filler)"]

    idea = StructuredIdea(
        problem_statement=problem_statement,
        goal=goal,
        audience=audience,
        task_type=task_type,
        constraints=constraints,
        output_format=output_format,
        tone=tone,
        must_include=must_include,
        assumptions=[
            "The raw idea reflects the real context; flag anything ambiguous instead of guessing silently",
        ],
        risks=[
            "Missing context may reduce precision",
            "Ambiguous goals can lead to generic output",
        ],
    )
    idea.role = _ROLE_BY_TYPE.get(task_type, _ROLE_BY_TYPE["general"])

    if not with_analysis:
        return idea
    analysis = analyze_raw_idea(text, idea, explicit_fields, signals)
    return idea, analysis


def parse_and_analyze(raw_text: str) -> tuple[StructuredIdea, PromptAnalysis]:
    result = parse_raw_idea(raw_text, with_analysis=True)
    assert isinstance(result, tuple)
    return result


def analyze_raw_idea(
    text: str, idea: StructuredIdea, explicit_fields: set[str], signals: list[str]
) -> PromptAnalysis:
    clarity = _score_clarity(text)
    specificity = _score_specificity(text)
    completeness, suggestions = _score_completeness(idea, explicit_fields, text)
    overall = round(clarity * 0.35 + specificity * 0.35 + completeness * 0.30)
    signal_tags = [f"task_type:{idea.task_type}"] + [f"keyword:{s}" for s in signals]
    if re.search(r"\d+", text):
        signal_tags.append("quantified")
    if explicit_fields:
        signal_tags.append("structured-input")
    return PromptAnalysis(
        task_type=idea.task_type,
        clarity_score=clarity,
        specificity_score=specificity,
        completeness_score=completeness,
        overall_score=overall,
        word_count=len(text.split()),
        detected_signals=sorted(set(signal_tags)),
        suggestions=suggestions,
    )


def _score_clarity(text: str) -> int:
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    avg_len = (sum(len(s.split()) for s in sentences) / max(len(sentences), 1)) if sentences else len(text.split())
    score = 100
    if avg_len > 28:
        score -= 25
    elif avg_len > 20:
        score -= 10
    vague_hits = sum(1 for w in _VAGUE_WORDS if re.search(rf"\b{w}\b", text.lower()))
    score -= min(vague_hits * 8, 32)
    if len(text.split()) < 8:
        score -= 15
    return max(score, 5)


def _score_specificity(text: str) -> int:
    score = 35
    if re.search(r"\d+", text):
        score += 20
    if re.search(r"\b(will|must|should|need to|has to)\b", text.lower()):
        score += 15
    if len(text.split()) >= 25:
        score += 15
    if ":" in text or "-" in text:
        score += 10
    if any(f in text.lower() for f in ("goal", "audience", "output", "constraint", "tone", "include")):
        score += 5
    return min(score, 100)


def _score_completeness(idea: StructuredIdea, parsed_fields: set[str], raw_text: str) -> tuple[int, list[str]]:
    checks = [
        ("goal", bool(idea.goal)),
        ("audience", "audience" in parsed_fields),
        ("constraints", "constraints" in parsed_fields),
        ("output format", "output_format" in parsed_fields),
        ("tone", "tone" in parsed_fields),
        ("must include", "must_include" in parsed_fields),
    ]
    filled = sum(1 for _, ok in checks)
    suggestions = [f"Add a '{name}' line for higher precision" for name, ok in checks if not ok]
    if re.search(r"\d", raw_text) is None:
        suggestions.append("Quantify targets (word counts, counts, deadlines) so the output is measurable")
    words = idea.problem_statement.lower().split()
    if len(words) < 12:
        suggestions.append("Expand the problem statement with context the model can anchor to")
    return round((filled / len(checks)) * 100), suggestions
