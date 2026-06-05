"""Classifier routing — assert entry_node maps each route to the right plan.

The structured LLM is stubbed to return a fixed RequestRoute; this verifies the
plumbing (route → plan), not the model's classification quality."""

import pytest

import agents.entry as entry_mod
from core.schemas import RequestRoute


class _StubLLM:
    def __init__(self, route_value: str) -> None:
        self._route_value = route_value

    def invoke(self, *args, **kwargs) -> RequestRoute:
        return RequestRoute(route=self._route_value)


@pytest.mark.parametrize(
    "route, expected_plan",
    [
        ("roles_only", ["scored"]),
        ("market_only", ["market_findings"]),
        ("market_then_roles", ["market_findings", "scored"]),
    ],
)
def test_entry_routes_to_expected_plan(monkeypatch, valid_profile, route, expected_plan):
    monkeypatch.setattr(entry_mod, "get_structured_llm", lambda schema: _StubLLM(route))

    out = entry_mod.entry_node(
        {"profile": valid_profile.model_dump(), "question": "any question"}
    )

    assert out == {"plan": expected_plan}
