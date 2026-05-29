"""route_next: walk the plan; first field that is unfilled AND whose worker is
not marked failed → that worker; otherwise END. Pure function."""

from langgraph.graph import END

from agents.supervisor import MARKET, ROLES, route_next


def test_first_unfilled_field_routes_to_its_worker():
    state = {"plan": ["scored"]}
    assert route_next(state) == ROLES


def test_filled_field_advances_to_end():
    state = {"plan": ["scored"], "scored": [{"list_position": 0}]}
    assert route_next(state) == END


def test_failed_worker_is_skipped_not_rerouted():
    # scored empty but roles failed → do not re-route a dead worker → END
    state = {"plan": ["scored"], "worker_status": {ROLES: "failed"}}
    assert route_next(state) == END


def test_two_step_plan_advances_to_second_worker():
    state = {
        "plan": ["market_findings", "scored"],
        "market_findings": [{"statement": "x"}],
    }
    assert route_next(state) == ROLES


def test_failed_first_worker_advances_to_second():
    # market failed, scored still pending → skip market, route to roles
    state = {
        "plan": ["market_findings", "scored"],
        "worker_status": {MARKET: "failed"},
    }
    assert route_next(state) == ROLES


def test_all_filled_ends():
    state = {
        "plan": ["market_findings", "scored"],
        "market_findings": [{"statement": "x"}],
        "scored": [{"list_position": 0}],
    }
    assert route_next(state) == END
