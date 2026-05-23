from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage

from agents.schemas import CandidatesSchema, ScoreSchema
from agents.tools import search_hn_job_postings
from core.config import (
    SCORE_DIMENSIONS,
    SCORE_MAX_CANDIDATES,
    SCORE_WEIGHTS,
    THRESHOLD_BANDS,
)
from core.llm import get_chat_llm, get_structured_llm

_FIND_SYS = (
    "You search Hacker News job postings for roles matching the candidate "
    "profile. Use the search tool; you may search more than once with refined "
    "queries. Return the postings you find, referring to each by list position."
)

_EXTRACT_SYS = (
    "From the search results below, extract each relevant posting as a "
    "candidate. Use the posting's list position as list_position and its full "
    "text as raw_text. Keep only postings plausibly relevant to the profile."
)

_SCORE_SYS = (
    "Score how well this single job posting matches the candidate profile. "
    "Score each dimension 0-5 and give brief reasoning. Do not invent a final "
    "score."
)


def _find(profile: dict) -> str:
    agent = create_agent(
        model=get_chat_llm(),
        tools=[search_hn_job_postings],
        system_prompt=_FIND_SYS,
    )
    result = agent.invoke(
        {"messages": [HumanMessage(f"Candidate profile: {profile}")]}
    )
    tool_msgs = [m.content for m in result["messages"]
                 if isinstance(m, ToolMessage)]
    return "\n\n".join(tool_msgs)



def _extract(search_text: str) -> list:
    llm = get_structured_llm(CandidatesSchema)
    out = llm.invoke(
        [{"role": "system", "content": _EXTRACT_SYS},
         HumanMessage(search_text)]
    )
    return out.candidates


def _score_one(candidate, profile: dict) -> ScoreSchema:
    llm = get_structured_llm(ScoreSchema)
    return llm.invoke(
        [{"role": "system", "content": _SCORE_SYS},
         HumanMessage(f"Profile: {profile}\n\nPosting:\n{candidate.raw_text}")]
    )


def _classify(candidate, score: ScoreSchema) -> dict:
    dims = {d: getattr(score, d) for d in SCORE_DIMENSIONS}
    total = sum(dims[d] * SCORE_WEIGHTS[d] for d in SCORE_DIMENSIONS)
    label = next(lbl for floor, lbl in THRESHOLD_BANDS if total >= floor)
    return {
        "list_position": candidate.list_position,
        "raw_text": candidate.raw_text,
        **dims,
        "reasoning": score.reasoning,
        "total": round(total, 2),
        "label": label,
    }


def roles_node(state: dict) -> dict:
    profile = state["profile"]
    search_text = _find(profile)
    candidates = _extract(search_text)[:SCORE_MAX_CANDIDATES]
    scored = [_classify(c, _score_one(c, profile)) for c in candidates]
    return {"scored": scored}