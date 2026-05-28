import langsmith as ls
from langgraph.graph import START, StateGraph
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.entry import entry_node
from agents.market import market_node
from agents.roles import roles_node
from agents.state import AgentState
from agents.supervisor import (
    ENTRY,
    FIELD_TO_WORKER,
    MARKET,
    ROLES,
    SUPERVISOR,
    route_next,
    supervisor_node,
)
from core.schemas import AgentResult, InvalidSeamInputError, NoResultsError, Profile
from core.validators import validate_langsmith_env

RECURSION_LIMIT = 10


def build_graph():
    g = StateGraph(AgentState)
    g.add_node(ENTRY, entry_node)
    g.add_node(SUPERVISOR, supervisor_node)
    g.add_node(MARKET, market_node)
    g.add_node(ROLES, roles_node)
    g.add_edge(START, ENTRY)
    g.add_edge(ENTRY, SUPERVISOR)
    g.add_conditional_edges(SUPERVISOR, route_next)
    g.add_edge(MARKET, SUPERVISOR)
    g.add_edge(ROLES, SUPERVISOR)
    return g.compile()


@traceable(name="job_market_analyzer.run")
def run(
    graph,
    question: str,
    profile: Profile,
    *,
    trace: bool = False,
    surface: str = "dev"
) -> AgentResult:
    validate_langsmith_env()
    if not question or not question.strip():
        raise InvalidSeamInputError("question must be a non-empty string")

    state = {
        "messages": [{"role": "user", "content": question}],
        "profile": profile.model_dump(),
        "question": question,
    }
    config = {
        "recursion_limit": RECURSION_LIMIT,
        "tags": [surface], 
        "metadata": {"surface": surface}
    }

    with ls.tracing_context(enabled=trace):
        final = graph.invoke(state, config=config)

    plan = final.get("plan", [])
    filled = [f for f in plan if final.get(f)]
    failed_workers = [FIELD_TO_WORKER[f] for f in plan
                      if final.get("worker_status", {}).get(FIELD_TO_WORKER[f]) == "failed"]

    if plan and not filled:
        raise NoResultsError(f"no planned worker produced data; failed={failed_workers}")

    status = "ok" if len(filled) == len(plan) else "partial"
    return _result(status=status, scored=final.get("scored"),
                   market_findings=final.get("market_findings"), trace=trace)


def _result(*,
            status, 
            scored=None,
            market_findings=None,
            error=None, 
            trace: bool
) -> AgentResult:
    run_id, run_url = None, None
    if trace:
        rt = get_current_run_tree()
        if rt is not None:
            run_id, run_url = str(rt.id), rt.get_url()
    return AgentResult(status=status, scored=scored, market_findings=market_findings,
                       error=error, run_id=run_id, run_url=run_url)