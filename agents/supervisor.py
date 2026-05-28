from langgraph.graph import END

MARKET = "market"
ROLES = "roles"
SUPERVISOR = "supervisor"
ENTRY = "entry"


MARKET_FINDINGS = "market_findings"
SCORED = "scored"

FIELD_TO_WORKER = {MARKET_FINDINGS: MARKET, SCORED: ROLES}


def supervisor_node(state: dict) -> dict:
    return state


def route_next(state: dict) -> str:
    worker_status = state.get("worker_status", {})
    for field in state["plan"]:
        worker = FIELD_TO_WORKER[field]
        if not state.get(field) and worker_status.get(worker) != "failed":
            return worker
    return END
