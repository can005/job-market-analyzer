"""Scoring eval — reasoning-quality layer (LLM judge).

Catches "right band via hallucination" — model gets the band right but for fake
reasons. Pure judge-driven metric, key-gated via evals.judge.get_judge(). When
no judge is available, the layer is skipped and the deterministic floor
(evals.scoring) still reports."""

from typing import Callable

from pydantic import BaseModel, Field

from evals.judge import judge_metadata

JudgeFn = Callable[[dict, str, str], dict]


class ReasoningAssessment(BaseModel):
    rubric_match: float = Field(
        ge=0.0,
        le=1.0,
        description="Does the rationale apply the four scoring dimensions?",
    )
    evidence_grounded: float = Field(
        ge=0.0,
        le=1.0,
        description="Is the rationale grounded in the posting (no hallucinated facts)?",
    )
    notes: str = Field(min_length=1)


_JUDGE_SYS = (
    "You evaluate the quality of a scoring rationale. Given a candidate "
    "profile, the job posting text, and the rationale to evaluate, return:\n"
    " - rubric_match: 0.0–1.0 — does the rationale apply the four scoring "
    "dimensions (skills, seniority, domain, logistics)?\n"
    " - evidence_grounded: 0.0–1.0 — does the rationale reference real content "
    "from the posting (no hallucinated facts)?\n"
    " - notes: brief justification."
)


def _format_user_msg(profile: dict, posting: str, rationale: str) -> str:
    return f"Profile: {profile}\n\nPosting:\n{posting}\n\nRationale:\n{rationale}"


def build_judge_fn(judge) -> JudgeFn:
    structured = judge.with_structured_output(ReasoningAssessment)

    def judge_fn(profile: dict, posting: str, rationale: str) -> dict:
        result = structured.invoke(
            [
                {"role": "system", "content": _JUDGE_SYS},
                {"role": "user", "content": _format_user_msg(profile, posting, rationale)},
            ]
        )
        return result.model_dump()

    return judge_fn


def evaluate_reasoning(cases: list[dict], scorer, judge_fn: JudgeFn | None = None) -> dict:
    if judge_fn is None:
        return {
            "summary": {"judge_skipped": True, **judge_metadata()},
            "per_case": [],
        }

    per_case = []
    for case in cases:
        predicted = scorer(case["profile"], case["candidate"])
        rationale = predicted.get("reasoning", "")
        posting = case["candidate"].get("raw_text", "")
        assessment = judge_fn(case["profile"], posting, rationale)
        per_case.append({"id": case["id"], **assessment})

    n = len(per_case)
    return {
        "summary": {
            "judge_skipped": False,
            "n_cases": n,
            "mean_rubric_match": sum(c["rubric_match"] for c in per_case) / n if n else 0.0,
            "mean_evidence_grounded": (
                sum(c["evidence_grounded"] for c in per_case) / n if n else 0.0
            ),
            **judge_metadata(),
        },
        "per_case": per_case,
    }
