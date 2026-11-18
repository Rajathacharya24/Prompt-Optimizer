import http.client
import json
import threading

from prompt_optimizer.spec_optimizer import optimize_to_spec
from prompt_optimizer.web import create_server


def test_spec_output_for_clear_idea() -> None:
    raw = (
        "Goal: Build a launch email for a new AI note-taking app. "
        "Audience: Startup founders. Constraints: 120 words max, no hype. "
        "Output: Subject line + body. Tone: Clear and practical."
    )
    result = optimize_to_spec(raw)

    assert not result.vague
    assert result.formatted.startswith("**Optimized Prompt:**\n```\n")
    assert "\n```\n\n**Assumptions:**" in result.formatted
    assert "Role:" in result.optimized_prompt
    assert "Goal:" in result.optimized_prompt
    assert "Context:" in result.optimized_prompt
    assert "Task steps:" in result.optimized_prompt
    assert "Rules:" in result.optimized_prompt
    assert "Output format:" in result.optimized_prompt
    assert result.assumptions
    assert result.quick_questions == []


def test_spec_output_for_vague_idea() -> None:
    result = optimize_to_spec("something")

    assert result.vague
    assert result.formatted.startswith("**Quick questions (optional):**")
    assert 1 <= len(result.quick_questions) <= 3
    assert result.optimized_prompt == ""
    assert "**Optimized Prompt:**" not in result.formatted


def test_api_endpoint_returns_formatted_text() -> None:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps({"idea": "Goal: Explain recursion to a beginner with examples. Output: bullets."})
        connection.request("POST", "/api/prompt-optimizer", body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        payload = json.loads(response.read())

        assert response.status == 200
        assert payload["formatted"] == payload["text"]
        assert payload["formatted"].startswith("**Optimized Prompt:**")
        assert payload["vague"] is False
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_endpoint_rejects_empty_idea() -> None:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        connection.request("POST", "/api/prompt-optimizer", "{}", {"Content-Type": "application/json"})
        response = connection.getresponse()
        assert response.status == 400
        response.read()
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
