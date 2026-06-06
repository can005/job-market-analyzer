import logging

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agents.supervisor import MARKET
from agents.tools import (
    collect_tool_output,
    list_market_dimensions,
    query_job_postings,
)
from core.config import AGENT_INNER_RECURSION_LIMIT
from core.errors import TRANSIENT_LLM_ERRORS
from core.llm import get_agent_chat_llm, get_structured_llm
from core.schemas import MarketSchema

logger = logging.getLogger(__name__)

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
        model=get_agent_chat_llm(),
        tools=[list_market_dimensions, query_job_postings],
        system_prompt=_MARKET_SYS,
    )
    result = agent.invoke(
        {"messages": [HumanMessage(question)]},
        config={"recursion_limit": AGENT_INNER_RECURSION_LIMIT},
    )
    query_text = collect_tool_output(result)
    logger.info("market.gather.done", extra={"query_text_chars": len(query_text)})
    return query_text


def _structure(query_text: str) -> list:
    llm = get_structured_llm(MarketSchema)
    out = llm.invoke([{"role": "system", "content": _FINDINGS_SYS}, HumanMessage(query_text)])
    logger.info("market.structure.done", extra={"findings": len(out.findings)})
    return out.findings


def market_node(state: dict) -> dict:
    try:
        query_text = _gather(state["question"])
        findings = _structure(query_text)
        logger.info("market.done", extra={"findings": len(findings)})
        return {"market_findings": [f.model_dump() for f in findings]}
    except TRANSIENT_LLM_ERRORS as e:
        logger.warning("market.transient", extra={"error_type": type(e).__name__})
        return {
            "worker_status": {MARKET: "failed"},
            "worker_errors": {MARKET: type(e).__name__},
        }
