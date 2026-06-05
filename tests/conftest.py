"""Shared fixtures + marker auto-apply. Single conftest at tests/ root."""

import pytest
from langgraph.graph import START, StateGraph

from agents.graph import build_graph
from agents.state import AgentState
from agents.supervisor import (
    ENTRY,
    MARKET,
    ROLES,
    SUPERVISOR,
    route_next,
    supervisor_node,
)
from core.schemas import Profile, ProfileSkill


# --- Tier markers by directory ------------------------------------------
def pytest_collection_modifyitems(config, items):
    """Auto-apply tier markers by folder. No hand-decorating each test.
    A test's tier = its heaviest dependency; the directory encodes that."""
    for item in items:
        path = str(item.fspath)
        if "/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in path:
            item.add_marker(pytest.mark.e2e)


# --- LangSmith env -------------------------------------------------------
@pytest.fixture(autouse=True)
def _langsmith_env(monkeypatch):
    """run() calls validate_langsmith_env() unconditionally, before the
    question check and regardless of trace. Inject dummy presence so unit
    tests stay green on any machine. Tracing itself is OFF in tests."""
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_PROJECT", "test-project")


# --- Profiles ------------------------------------------------------------
@pytest.fixture
def valid_profile() -> Profile:
    """Yields the Pydantic model instance. Tests call .model_dump() when they
    need the dict — keeps the seam boundary honest, never hand-write a dict."""
    return Profile(
        skills=[
            ProfileSkill(skill="C++", years=10),
            ProfileSkill(skill="Python", years=5),
        ],
        domain="backend systems",
        logistics="remote, EU timezone",
    )


# --- Graph fixtures ------------------------------------------------------
@pytest.fixture
def compiled_graph():
    """Real compiled graph. Function-scope: compile is cheap, isolation matters.
    Used by e2e (real nodes hit LLM/DB)."""
    return build_graph()


@pytest.fixture
def make_stub_graph():
    """Factory: build a graph with fake node fns (no LLM/DB) wired exactly like
    the real one, so the REAL route_next + recursion backstop drive it.

    Override any of entry/roles/market; defaults fill their field once."""

    def _make(entry_fn=None, roles_fn=None, market_fn=None):
        entry_fn = entry_fn or (lambda s: {"plan": ["scored"]})
        roles_fn = roles_fn or (lambda s: {"scored": [{"hn_id": 0}]})
        market_fn = market_fn or (lambda s: {"market_findings": [{"statement": "x"}]})

        g = StateGraph(AgentState)
        g.add_node(ENTRY, entry_fn)
        g.add_node(SUPERVISOR, supervisor_node)
        g.add_node(ROLES, roles_fn)
        g.add_node(MARKET, market_fn)
        g.add_edge(START, ENTRY)
        g.add_edge(ENTRY, SUPERVISOR)
        g.add_conditional_edges(SUPERVISOR, route_next)
        g.add_edge(ROLES, SUPERVISOR)
        g.add_edge(MARKET, SUPERVISOR)
        return g.compile()

    return _make
