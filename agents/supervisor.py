import logging

from langgraph.graph import END

logger = logging.getLogger(__name__)

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
        if field not in state and worker_status.get(worker) != "failed":
            logger.info("supervisor.route", extra={"next": worker})
            return worker
    logger.info("supervisor.route", extra={"next": "END"})
    return END
