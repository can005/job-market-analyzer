from typing import Literal

from pydantic import BaseModel, Field

from core.config import SCORE_DIMENSIONS


# --- Profile (seam) ------------------------------------------------------
class ProfileSkill(BaseModel):
    skill: str
    years: int


class Profile(BaseModel):
    skills: list[ProfileSkill]
    domain: str
    logistics: str


# --- Roles worker: extracted candidates ----------------------------------
class RequiredSkill(BaseModel):
    skill: str
    years_required: int | None
    level: Literal["none", "familiar", "proficient", "strong", "expert"]
    matched_profile_skill: str | None


class Candidate(BaseModel):
    list_position: int = Field(ge=0)
    raw_text: str = Field(min_length=1)
    required_skills: list[RequiredSkill]


class CandidatesSchema(BaseModel):
    """Structured-output target for the find call (wrapper holds the list)."""
    candidates: list[Candidate]


# --- Scoring -------------------------------------------------------------
class SkillSeniorityScore(BaseModel):
    skill: str
    score: int = Field(ge=0, le=5)


class ScoreSchema(BaseModel):
    skills_match: int = Field(ge=0, le=5)
    seniority_match: list[SkillSeniorityScore]
    domain_match: int = Field(ge=0, le=5)
    logistics_match: int = Field(ge=0, le=5)
    reasoning: str = Field(min_length=1)


_score_fields = frozenset(ScoreSchema.model_fields) - {"reasoning"}
if _score_fields != frozenset(SCORE_DIMENSIONS):
    raise RuntimeError(
        f"ScoreSchema dimensions {sorted(_score_fields)} != "
        f"SCORE_DIMENSIONS {sorted(SCORE_DIMENSIONS)}"
    )


# --- Market worker: structured findings ----------------------------------
class MarketFinding(BaseModel):
    statement: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class MarketSchema(BaseModel):
    findings: list[MarketFinding]


# --- Entry classification → drives plan ----------------------------------
class RequestRoute(BaseModel):
    route: Literal["roles_only", "market_only", "market_then_roles"]


# --- Seam boundary: result + typed exceptions ----------------------------
class AgentResult(BaseModel):
    status: Literal["ok", "partial", "error"]
    scored: list[dict] | None = None           
    market_findings: list[dict] | None = None              
    run_id: str | None = None                 
    run_url: str | None = None


class NoResultsError(Exception):
    """Raised by run() when no planned worker produced data."""


class InvalidSeamInputError(Exception):
    """Raised by run() for invalid seam input (e.g. empty question)."""