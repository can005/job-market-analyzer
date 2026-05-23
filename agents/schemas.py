from typing import Literal

from pydantic import BaseModel, Field

from core.config import SCORE_DIMENSIONS


# --- Scoring -------------------------------------------------------------
class ScoreSchema(BaseModel):
    skills_match: int = Field(ge=0, le=5)
    seniority_match: int = Field(ge=0, le=5)
    domain_match: int = Field(ge=0, le=5)
    logistics_match: int = Field(ge=0, le=5)
    reasoning: str = Field(min_length=1)


_score_fields = frozenset(ScoreSchema.model_fields) - {"reasoning"}
if _score_fields != frozenset(SCORE_DIMENSIONS):
    raise RuntimeError(
        f"ScoreSchema dimensions {sorted(_score_fields)} != "
        f"SCORE_DIMENSIONS {sorted(SCORE_DIMENSIONS)}"
    )


# --- Roles worker: find → structured candidates --------------------------
class Candidate(BaseModel):
    list_position: int = Field(ge=0)
    raw_text: str = Field(min_length=1)


class CandidatesSchema(BaseModel):
    """Structured-output target for the find call (wrapper holds the list)."""
    candidates: list[Candidate]


# --- Market worker: structured findings ----------------------------------
# Thin by intent: real Indeed columns confirmed at Step 5. Tighten then.
class MarketFinding(BaseModel):
    statement: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class MarketSchema(BaseModel):
    findings: list[MarketFinding]


# --- Entry classification → drives plan ----------------------------------
class RequestRoute(BaseModel):
    route: Literal["roles_only", "market_only", "market_then_roles"]