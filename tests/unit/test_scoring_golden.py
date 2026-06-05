"""Golden-set scoring regression — realistic profile + canned ScoreSchema → expected band.

Locks in the user-visible band labels against changes to weights or thresholds.
Distinct from test_classify.py (which probes the band-floor boundaries with
synthetic numbers); this file uses naturalistic raw_text and full per-dimension
scores so the regression bites if weighting semantics drift."""

import pytest

from agents.roles import _classify
from core.schemas import Candidate, ScoreSchema, SkillSeniorityScore


def _candidate(raw_text: str) -> Candidate:
    return Candidate(hn_id=0, raw_text=raw_text, required_skills=[])


def _score(skills: int, seniority: list[int], domain: int, logistics: int) -> ScoreSchema:
    return ScoreSchema(
        skills_match=skills,
        seniority_match=[SkillSeniorityScore(skill="s", score=v) for v in seniority],
        domain_match=domain,
        logistics_match=logistics,
        reasoning="golden",
    )


GOLDEN_CASES = [
    pytest.param(
        "ACME Robotics | Senior C++ backend | remote EU",
        _score(skills=5, seniority=[5], domain=5, logistics=5),
        "strong",
        5.0,
        id="strong_full_alignment",
    ),
    pytest.param(
        "WidgetCo | Python backend | hybrid Berlin",
        _score(skills=4, seniority=[3, 3], domain=3, logistics=2),
        "moderate",
        3.25,
        id="moderate_solid_but_logistics_friction",
    ),
    pytest.param(
        "QuantHedge | Kotlin Android | onsite NYC",
        _score(skills=1, seniority=[2], domain=1, logistics=0),
        "weak",
        1.1,
        id="weak_off_target_domain_and_logistics",
    ),
]


@pytest.mark.parametrize("raw_text, score, expected_label, expected_total", GOLDEN_CASES)
def test_golden_band(raw_text, score, expected_label, expected_total):
    out = _classify(_candidate(raw_text), score)
    assert out["label"] == expected_label
    assert out["total"] == expected_total
