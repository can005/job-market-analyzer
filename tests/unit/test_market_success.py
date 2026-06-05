"""market_node happy path with LLM helpers stubbed.

Asserts the worker assembles _gather → _structure into the expected
`market_findings` shape — the success-path counterpart to test_worker_failure."""

import agents.market as market_mod
from core.schemas import MarketFinding


def test_market_success_returns_findings(monkeypatch):
    findings = [
        MarketFinding(statement="postings trending up", evidence="index 100 → 110 over Q1"),
        MarketFinding(statement="tech sector outpaces aggregate", evidence="tech +12%, agg +5%"),
    ]
    monkeypatch.setattr(market_mod, "_gather", lambda question: "query results text")
    monkeypatch.setattr(market_mod, "_structure", lambda query_text: findings)

    out = market_mod.market_node({"question": "what are recent trends?"})

    assert out == {
        "market_findings": [
            {"statement": "postings trending up", "evidence": "index 100 → 110 over Q1"},
            {"statement": "tech sector outpaces aggregate", "evidence": "tech +12%, agg +5%"},
        ]
    }
