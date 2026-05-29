"""Failure-path injection. Monkeypatch an internal call to RAISE, then assert the
node's except-branch writes the worker_status marker. This tests error handling,
NOT the model — so it's unit (the exception comes from a stub, no LLM is called).

Distinct from faking LLM *success*, which would require the model and be e2e."""

import agents.market as market_mod
import agents.roles as roles_mod
from agents.supervisor import MARKET, ROLES


def _boom(*args, **kwargs):
    raise RuntimeError("injected failure")


def test_roles_node_writes_failed_marker(monkeypatch):
    monkeypatch.setattr(roles_mod, "_find", _boom)
    out = roles_mod.roles_node({"profile": {"skills": [], "domain": "d", "logistics": "l"}})
    assert out == {"worker_status": {ROLES: "failed"}}
    assert "scored" not in out


def test_market_node_writes_failed_marker(monkeypatch):
    monkeypatch.setattr(market_mod, "_gather", _boom)
    out = market_mod.market_node({"question": "any trend question"})
    assert out == {"worker_status": {MARKET: "failed"}}
    assert "market_findings" not in out


def test_roles_failure_in_scoring_also_marks(monkeypatch):
    # failure later in the pipeline (scoring) is caught the same way
    monkeypatch.setattr(roles_mod, "_find", lambda profile: "search text")
    monkeypatch.setattr(roles_mod, "_extract", _boom)
    out = roles_mod.roles_node({"profile": {"skills": [], "domain": "d", "logistics": "l"}})
    assert out == {"worker_status": {ROLES: "failed"}}
