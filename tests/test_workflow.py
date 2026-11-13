from prompt_optimizer.workflow import optimize_raw_idea


def test_optimize_raw_idea_with_labels() -> None:
    raw = """
    Goal: Create onboarding email copy
    Audience: New SaaS users
    Constraints: 120 words max; simple language
    Output: Subject line + body
    Tone: Helpful and clear
    Must Include: Welcome message; setup steps
    """

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal == "Create onboarding email copy"
    assert result.structured_idea.audience == "New SaaS users"
    assert "120 words max" in result.structured_idea.constraints
    assert "setup steps" in [v.lower() for v in result.structured_idea.must_include]
    assert "Execution Steps" in result.optimized_prompt


def test_optimize_raw_idea_without_labels() -> None:
    raw = "Need a concise migration note for enterprise customers and avoid hype language."

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal
    assert result.structured_idea.problem_statement
    assert "Task" in result.optimized_prompt


def test_optimize_raw_idea_with_inline_labels() -> None:
    raw = (
        "Goal: Draft a product update note. Audience: Existing users. "
        "Constraints: 80 words max; no hype. Output: heading + 3 bullets. "
        "Tone: confident and clear. Must Include: benefit; next step"
    )

    result = optimize_raw_idea(raw)

    assert result.structured_idea.goal == "Draft a product update note."
    assert result.structured_idea.audience == "Existing users."
    assert "80 words max" in result.structured_idea.constraints
    assert "next step" in [v.lower() for v in result.structured_idea.must_include]
