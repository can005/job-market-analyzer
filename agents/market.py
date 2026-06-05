from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agents.supervisor import MARKET
from agents.tools import (
    collect_tool_output,
    list_market_dimensions,
    query_job_postings,
)
from core.errors import TRANSIENT_LLM_ERRORS
from core.llm import get_chat_llm, get_structured_llm
from core.schemas import MarketSchema

_MARKET_SYS = (
    "You answer job-market TREND questions using the Indeed index tables "
    "(US only; index time series, not job counts). First call "
    "list_market_dimensions to get valid variable/sector values, then write "
    "read-only SELECT queries with query_job_postings. Filter on real values. "
    "Anchor findings to actual index movements over dates."
)

_FINDINGS_SYS = (
    "From the query results below, extract market findings. Each finding is a "
    "trend statement plus the data backing it (index values and dates)."
)


def _gather(question: str) -> str:
    agent = create_agent(
        model=get_chat_llm(),
        tools=[list_market_dimensions, query_job_postings],
        system_prompt=_MARKET_SYS,
    )
    result = agent.invoke({"messages": [HumanMessage(question)]})
    return collect_tool_output(result)


def _structure(query_text: str) -> list:
    llm = get_structured_llm(MarketSchema)
    out = llm.invoke([{"role": "system", "content": _FINDINGS_SYS}, HumanMessage(query_text)])
    return out.findings


def market_node(state: dict) -> dict:
    try:
        query_text = _gather(state["question"])
        findings = _structure(query_text)
        return {"market_findings": [f.model_dump() for f in findings]}
    except TRANSIENT_LLM_ERRORS as e:
        return {
            "worker_status": {MARKET: "failed"},
            "worker_errors": {MARKET: type(e).__name__},
        }
