"""route_next + the roles refinement policy. Pure function over state.

market: route while its field is unfilled and the worker has not failed.
roles: first dispatch always; then re-dispatch (broadened) until a termination
guard trips — count cap, good-enough strong count, or the cost-ceiling proxy."""

from langgraph.graph import END

from agents.supervisor import MARKET, ROLES, route_next
from core.config import COST_CEILING_CANDIDATES, GOOD_ENOUGH_STRONG, MAX_REFINE_PASSES


def _scored(label, n):
    return [{"hn_id": i, "label": label} for i in range(n)]


# --- roles: first dispatch + re-dispatch -------------------------------------


def test_roles_first_dispatch_when_never_run():
    assert route_next({"plan": ["scored"]}) == ROLES


def test_roles_redispatch_when_weak_and_under_caps():
    state = {"plan": ["scored"], "refine_passes": 1, "scored": _scored("weak", 2)}
    assert route_next(state) == ROLES


# --- roles: termination guards (whichever trips first) -----------------------


def test_roles_stops_on_good_enough():
    state = {
        "plan": ["scored"],
        "refine_passes": 1,
        "scored": _scored("strong", GOOD_ENOUGH_STRONG),
    }
    assert route_next(state) == END


def test_roles_stops_on_count_cap():
    state = {
        "plan": ["scored"],
        "refine_passes": MAX_REFINE_PASSES,
        "scored": _scored("weak", 1),
    }
    assert route_next(state) == END


def test_roles_stops_on_cost_ceiling():
    state = {
        "plan": ["scored"],
        "refine_passes": 1,
        "scored": _scored("weak", COST_CEILING_CANDIDATES),
    }
    assert route_next(state) == END


def test_failed_roles_is_not_redispatched():
    state = {"plan": ["scored"], "worker_status": {ROLES: "failed"}}
    assert route_next(state) == END


# --- market: single-run semantics --------------------------------------------


def test_market_routes_when_unfilled():
    assert route_next({"plan": ["market_findings"]}) == MARKET


def test_market_advances_to_end_when_filled():
    state = {"plan": ["market_findings"], "market_findings": [{"statement": "x"}]}
    assert route_next(state) == END


def test_failed_market_advances_to_end():
    state = {"plan": ["market_findings"], "worker_status": {MARKET: "failed"}}
    assert route_next(state) == END


# --- two-step plan: market then roles ----------------------------------------


def test_two_step_advances_to_roles_after_market():
    state = {"plan": ["market_findings", "scored"], "market_findings": [{"statement": "x"}]}
    assert route_next(state) == ROLES


def test_failed_first_worker_advances_to_roles():
    state = {"plan": ["market_findings", "scored"], "worker_status": {MARKET: "failed"}}
    assert route_next(state) == ROLES


def test_two_step_ends_when_market_filled_and_roles_good_enough():
    state = {
        "plan": ["market_findings", "scored"],
        "market_findings": [{"statement": "x"}],
        "refine_passes": 1,
        "scored": _scored("strong", GOOD_ENOUGH_STRONG),
    }
    assert route_next(state) == END
