from prompt_optimizer.interview import apply_interview, build_interview


def test_build_interview_skips_provided_fields() -> None:
    raw = """
    Goal: Create onboarding email copy
    Audience: New SaaS users
    Tone: Helpful and clear
    """
    plan = build_interview(raw)

    ids = [q.id for q in plan.questions]
    assert "audience" not in ids
    assert "tone" not in ids
    assert "output_format" in ids
    assert "constraints" in ids
    assert "depth" in ids
    assert plan.detected_type == "writing"
    assert plan.type_options[0].value == "auto"
    assert any(o.value == "marketing" for o in plan.type_options)


def test_build_interview_vague_idea_asks_everything() -> None:
    plan = build_interview("something about my project files")

    ids = [q.id for q in plan.questions]
    assert "audience" in ids
    assert "output_format" in ids
    assert "tone" in ids
    assert plan.detected_type == "general"


def test_apply_interview_with_answers() -> None:
    raw = "Build a habit tracker web app with a dashboard"
    plan = build_interview(raw)
    answers = {
        "audience": "Complete beginner",
        "output_format": "Working code with setup/run instructions",
        "tone": "Friendly and conversational",
        "constraints": "No external dependencies",
        "must_include": "setup steps; daily view",
        "depth": "deep",
    }

    result = apply_interview(raw, answers, "auto")

    idea = result.structured_idea
    assert idea.audience == "Complete beginner"
    assert "setup/run instructions" in idea.output_format
    assert "No external dependencies" in idea.constraints
    assert "daily view" in idea.must_include
    assert any("thorough" in c for c in idea.constraints)
    assert "# PROCESS" in result.optimized_prompt
    assert result.analysis.task_type == "code"
    assert any("depth set to deep dive" in i for i in result.improvements_applied)


def test_apply_interview_type_switch() -> None:
    raw = "Build a habit tracker web app with a dashboard"

    result = apply_interview(raw, {"depth": "standard"}, "planning")

    assert result.structured_idea.task_type == "planning"
    assert "project strategist" in result.structured_idea.role
    assert any("task type switched" in i for i in result.improvements_applied)


def test_apply_interview_all_skipped_uses_defaults() -> None:
    raw = "Explain recursion to a beginner with examples"

    result = apply_interview(raw, {}, "")

    assert result.structured_idea.task_type == "learning"
    assert result.improvements_applied == ["no changes from interview — defaults kept"]
    assert "# OBJECTIVE" in result.optimized_prompt


def test_interview_plan_serializes() -> None:
    plan = build_interview("Write a blog post about AI, 500 words")
    data = plan.to_dict()
    assert data["detected_type"] == "writing"
    assert all("prompt" in q for q in data["questions"])
    assert all("options" in q for q in data["questions"])
