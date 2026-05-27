from langchain_core.messages import HumanMessage

from core.llm import get_structured_llm
from core.schemas import RequestRoute
from core.validators import validate_profile

ROUTE_TO_PLAN = {
    "roles_only": ["scored"],
    "market_only": ["market_findings"],
    "market_then_roles": ["market_findings", "scored"],
}

_CLASSIFY_SYS = (
    "Classify the user's request into one route:\n"
    "- roles_only: wants matching job roles/postings.\n"
    "- market_only: wants job-market trends/statistics.\n"
    "- market_then_roles: wants market context AND roles."
)


def entry_node(state: dict) -> dict:
    validate_profile(state.get("profile"))

    last = state["messages"][-1].content
    llm = get_structured_llm(RequestRoute)
    route = llm.invoke(
        [{"role": "system", "content": _CLASSIFY_SYS}, HumanMessage(last)]
    ).route

    return {"plan": ROUTE_TO_PLAN[route]}