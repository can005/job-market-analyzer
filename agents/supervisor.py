import logging

from langgraph.graph import END

from core.config import COST_CEILING_CANDIDATES, GOOD_ENOUGH_STRONG, MAX_REFINE_PASSES

logger = logging.getLogger(__name__)

MARKET = "market"
ROLES = "roles"
SUPERVISOR = "supervisor"
ENTRY = "entry"


MARKET_FINDINGS = "market_findings"
SCORED = "scored"

FIELD_TO_WORKER = {MARKET_FINDINGS: MARKET, SCORED: ROLES}


def supervisor_node(state: dict) -> dict:
    return {}


def _roles_should_run(state: dict) -> bool:
    if state.get("worker_status", {}).get(ROLES) == "failed":
        return False
    passes = state.get("refine_passes", 0)
    if passes == 0:
        return True
    if passes >= MAX_REFINE_PASSES:
        return False
    scored = state.get("scored", [])
    if len(scored) >= COST_CEILING_CANDIDATES:
        return False
    strong = sum(1 for s in scored if s.get("label") == "strong")
    return strong < GOOD_ENOUGH_STRONG


def route_next(state: dict) -> str:
    worker_status = state.get("worker_status", {})
    for field in state["plan"]:
        worker = FIELD_TO_WORKER[field]
        if worker == ROLES:
            if _roles_should_run(state):
                logger.info(
                    "supervisor.route",
                    extra={"next": ROLES, "refine_passes": state.get("refine_passes", 0)},
                )
                return ROLES
        elif field not in state and worker_status.get(worker) != "failed":
            logger.info("supervisor.route", extra={"next": worker})
            return worker
    logger.info("supervisor.route", extra={"next": "END"})
    return END
