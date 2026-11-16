from prompt_optimizer.workflow import optimize_raw_idea


def test_optimize_raw_idea_with_labels() -> None:
    raw = """
    Goal: Create onboarding email copy
    Audience: New SaaS users
    Constraints: 120 words max; simple language
    Output: Subject line + body
    Tone: Helpful and clear
    Must Include: welcome message; setup steps
    """

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal.casefold() == "create onboarding email copy"
    assert result.structured_idea.audience.casefold() == "new saas users"
    assert "120 words max" in result.structured_idea.constraints
    assert "setup steps" in [v.lower() for v in result.structured_idea.must_include]
    assert "# PROCESS" in result.optimized_prompt
    assert "# OBJECTIVE" in result.optimized_prompt
    assert result.analysis is not None
    assert result.analysis.completeness_score == 100


def test_optimize_raw_idea_without_labels() -> None:
    raw = "Need a concise migration note for enterprise customers and avoid hype language."

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal
    assert result.structured_idea.problem_statement
    assert "# CONTEXT" in result.optimized_prompt
    assert result.analysis is not None
    assert "structured-input" not in result.analysis.detected_signals


def test_optimize_raw_idea_with_inline_labels() -> None:
    raw = (
        "Goal: Draft a product update note. Audience: Existing users. "
        "Constraints: 80 words max; no hype. Output: heading + 3 bullets. "
        "Tone: confident and clear. Must Include: benefit; next step"
    )

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal.casefold() == "draft a product update note"
    assert result.structured_idea.audience.casefold() == "existing users"
    assert "80 words max" in result.structured_idea.constraints
    assert "next step" in [v.lower() for v in result.structured_idea.must_include]


def test_task_type_detection() -> None:
    result = optimize_raw_idea("Build a web app that tracks my daily habits and shows a dashboard")
    assert result.structured_idea.task_type == "code"
    assert "software engineer" in result.structured_idea.role

    result = optimize_raw_idea("Explain recursion to a beginner with examples")
    assert result.structured_idea.task_type == "learning"
    assert "educator" in result.structured_idea.role


def test_analysis_scores_in_range() -> None:
    result = optimize_raw_idea("Write a blog post about AI, 500 words, friendly tone")
    a = result.analysis
    assert 0 <= a.overall_score <= 100
    assert 0 <= a.clarity_score <= 100
    assert 0 <= a.specificity_score <= 100
    assert a.word_count > 0
