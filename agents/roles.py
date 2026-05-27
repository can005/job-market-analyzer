from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from agents.tools import collect_tool_output, search_hn_job_postings
from core.config import (
    SCORE_DIMENSIONS,
    SCORE_MAX_CANDIDATES,
    SCORE_WEIGHTS,
    THRESHOLD_BANDS,
)
from core.llm import get_chat_llm, get_structured_llm
from core.schemas import CandidatesSchema, ScoreSchema

_FIND_SYS = (
    "You search Hacker News job postings for roles matching the candidate "
    "profile. Use the search tool; you may search more than once with refined "
    "queries. Return the postings you find, referring to each by list position."
)

_EXTRACT_SYS = (
    "From the search results below, extract each relevant posting as a "
    "candidate. Use the posting's list position as list_position and its full "
    "text as raw_text. Keep only postings plausibly relevant to the profile.\n"
    "\n"
    "For each candidate, populate required_skills — one entry per skill the "
    "posting requires (technical and non-technical alike; let the posting "
    "speak for itself).\n"
    "\n"
    "Each required_skills entry has two independent axes — capture both, "
    "never collapse one into the other:\n"
    "  - years_required: integer if the posting states a number "
    "(e.g. '5+ years C++' → 5); null otherwise. Do not invent a number from "
    "a proficiency word.\n"
    "  - level: the posting's proficiency word, one of "
    "[none, familiar, proficient, strong, expert]. Use 'none' when the "
    "posting states no proficiency word. Do not invent a word from a number.\n"
    "\n"
    "Also populate matched_profile_skill: the profile skill this posting "
    "skill aligns to semantically (e.g. posting 'C++17' → profile 'C++'). "
    "Use null when no profile skill aligns."
)

_SCORE_SYS = (
    "Score how well this single job posting matches the candidate profile. "
    "You will be given the profile, the posting's full text, and the "
    "posting's extracted required_skills.\n"
    "\n"
    "Return four dimensions. Three are global integers 0-5. One "
    "(seniority_match) is a list with one {skill, score} entry per "
    "required_skills entry, in the same order. Use the anchors below "
    "strictly — reserve 5 for standouts, do not pile scores at 3. Also "
    "give brief reasoning. Do not compute a final total.\n"
    "\n"
    "skills_match (global — profile's coverage of the posting's required skill set):\n"
    "  0 — profile covers none of the posting's required skills.\n"
    "  1 — covers one peripheral skill; core skills missing.\n"
    "  2 — covers some skills but misses the main one(s).\n"
    "  3 — covers the core skills; gaps on secondary ones.\n"
    "  4 — covers all required skills; one or two are weak matches semantically.\n"
    "  5 — covers every required skill with strong semantic alignment.\n"
    "\n"
    "seniority_match (per-skill — for each required_skills entry, judge "
    "candidate's profile years against the posting's years_required and level):\n"
    "  0 — matched_profile_skill is null.\n"
    "  1 — has the skill but years far below what the posting asks.\n"
    "  2 — has the skill, clearly under the bar.\n"
    "  3 — meets the bar approximately; close call either way.\n"
    "  4 — comfortably meets the bar.\n"
    "  5 — well beyond the bar; standout depth.\n"
    "\n"
    "domain_match (global — profile.domain vs posting's domain/industry):\n"
    "  0 — unrelated domain.\n"
    "  1 — adjacent but different industry.\n"
    "  2 — overlapping domain, different focus.\n"
    "  3 — same broad domain, different sub-area.\n"
    "  4 — same domain and sub-area.\n"
    "  5 — exact domain fit with standout relevance.\n"
    "\n"
    "logistics_match (global — profile.logistics vs the posting's logistical constraints):\n"
    "  0 — incompatible.\n"
    "  1 — major mismatch with possible workaround.\n"
    "  2 — partial mismatch on a key constraint.\n"
    "  3 — compatible on the main constraint, friction on secondary ones.\n"
    "  4 — fully compatible; minor preferences differ.\n"
    "  5 — perfect logistical fit."
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
    return collect_tool_output(result)


def _extract(search_text: str, profile: dict) -> list:
    llm = get_structured_llm(CandidatesSchema)
    out = llm.invoke(
        [{"role": "system", "content": _EXTRACT_SYS},
         HumanMessage(f"Profile: {profile}\n\nSearch results:\n{search_text}")]
    )
    return out.candidates


def _score_one(candidate, profile: dict) -> ScoreSchema:
    llm = get_structured_llm(ScoreSchema)
    return llm.invoke(
        [{"role": "system", "content": _SCORE_SYS},
         HumanMessage(
             f"Profile: {profile}\n\n"
             f"Required skills: {[rs.model_dump() for rs in candidate.required_skills]}\n\n"
             f"Posting:\n{candidate.raw_text}"
         )]
    )


def _classify(candidate, score: ScoreSchema) -> dict:
    seniority_scores = [s.score for s in score.seniority_match]
    seniority_avg = (
        sum(seniority_scores) / len(seniority_scores) if seniority_scores else 0
    )

    dims = {
        "skills_match": score.skills_match,
        "seniority_match": seniority_avg,
        "domain_match": score.domain_match,
        "logistics_match": score.logistics_match,
    }
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
    candidates = _extract(search_text, profile)[:SCORE_MAX_CANDIDATES]
    scored = [_classify(c, _score_one(c, profile)) for c in candidates]
    return {"scored": scored}