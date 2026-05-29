"""Seam-level unit tests. Everything goes through run() (matches the locked
"all tests run through run" rule), but with STUB graphs — fake node fns, no
LLM/DB — so the real route_next + run() status logic are what's exercised.

Status contract (from run()):
- plan filled completely        → "ok"
- some but not all filled        → "partial"
- planned but nothing filled     → NoResultsError
- empty question                 → InvalidSeamInputError
- graph never settles            → GraphRecursionError propagates (uncaught)
"""

import pytest
from langgraph.errors import GraphRecursionError

from agents.graph import run
from agents.supervisor import ROLES


def test_empty_question_raises_invalid_seam_input(make_stub_graph, valid_profile):
    from core.schemas import InvalidSeamInputError

    graph = make_stub_graph()
    with pytest.raises(InvalidSeamInputError):
        run(graph, "   ", valid_profile)


def test_ok_when_plan_fully_filled(make_stub_graph, valid_profile):
    graph = make_stub_graph(
        entry_fn=lambda s: {"plan": ["scored"]},
        roles_fn=lambda s: {"scored": [{"list_position": 0}]},
    )
    result = run(graph, "find roles", valid_profile)
    assert result.status == "ok"
    assert result.scored == [{"list_position": 0}]


def test_partial_when_one_worker_fails(make_stub_graph, valid_profile):
    graph = make_stub_graph(
        entry_fn=lambda s: {"plan": ["market_findings", "scored"]},
        market_fn=lambda s: {"market_findings": [{"statement": "trend"}]},
        roles_fn=lambda s: {"worker_status": {ROLES: "failed"}},
    )
    result = run(graph, "market then roles", valid_profile)
    assert result.status == "partial"
    assert result.market_findings == [{"statement": "trend"}]
    assert result.scored is None


def test_no_results_error_when_nothing_filled(make_stub_graph, valid_profile):
    from core.schemas import NoResultsError

    graph = make_stub_graph(
        entry_fn=lambda s: {"plan": ["scored"]},
        roles_fn=lambda s: {"worker_status": {ROLES: "failed"}},
    )
    with pytest.raises(NoResultsError):
        run(graph, "find roles", valid_profile)


def test_recursion_backstop_trips(make_stub_graph, valid_profile):
    # roles never fills 'scored' and never marks failed → route_next loops
    # supervisor↔roles until recursion_limit → GraphRecursionError propagates.
    graph = make_stub_graph(
        entry_fn=lambda s: {"plan": ["scored"]},
        roles_fn=lambda s: {},
    )
    with pytest.raises(GraphRecursionError):
        run(graph, "find roles", valid_profile)
