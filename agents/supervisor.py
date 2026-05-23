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
    for field in state["plan"]:
        if not state.get(field):
            return FIELD_TO_WORKER[field]
    return END