from langgraph.graph import START, StateGraph

from agents.entry import entry_node
from agents.market import market_node
from agents.roles import roles_node
from agents.state import AgentState
from agents.supervisor import (
    ENTRY,
    MARKET,
    ROLES,
    SUPERVISOR,
    route_next,
    supervisor_node,
)

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

def run(graph, message: str, profile: dict):
    state = {"messages": [{"role": "user", "content": message}], "profile": profile}
    return graph.invoke(state, config={"recursion_limit": RECURSION_LIMIT})