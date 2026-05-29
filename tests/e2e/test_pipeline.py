"""E2E tier — full real graph through the seam. Hits the LLM (and DB), so it is
slow and nondeterministic; manual/local only, never in routine CI. Fails loud if
OPENAI_API_KEY is unset (fail-within-tier). Marked 'e2e' automatically by directory.

This is a smoke test: it asserts the seam contract holds end to end, not exact
content (which the model varies)."""

from agents.graph import run


def test_roles_request_runs_end_to_end(compiled_graph, valid_profile):
    result = run(compiled_graph, "Find me C++ backend roles", valid_profile)
    assert result.status in {"ok", "partial"}
    # a roles-only or market-then-roles plan should produce scored on success
    if result.status == "ok":
        assert result.scored is not None


def test_market_request_runs_end_to_end(compiled_graph, valid_profile):
    result = run(
        compiled_graph,
        "What are the recent trends in US job postings?",
        valid_profile,
    )
    assert result.status in {"ok", "partial"}
