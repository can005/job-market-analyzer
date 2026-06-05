"""roles_node happy path with LLM helpers stubbed.

Asserts the worker assembles _find → _extract → _score_one → _classify into the
expected `scored` shape — this is the success-path counterpart to the
failure-path tests in test_worker_failure.py."""

import agents.roles as roles_mod
from core.config import SCORE_MAX_CANDIDATES
from core.schemas import Candidate, ScoreSchema, SkillSeniorityScore


def _strong_score() -> ScoreSchema:
    return ScoreSchema(
        skills_match=4,
        seniority_match=[SkillSeniorityScore(skill="Python", score=4)],
        domain_match=4,
        logistics_match=4,
        reasoning="strong match across all dimensions",
    )


def test_roles_success_returns_scored_list(monkeypatch, valid_profile):
    candidates = [
        Candidate(list_position=0, raw_text="ACME | Backend Engineer", required_skills=[]),
        Candidate(list_position=1, raw_text="WidgetCo | Python dev", required_skills=[]),
    ]
    monkeypatch.setattr(roles_mod, "_find", lambda profile: "search results text")
    monkeypatch.setattr(roles_mod, "_extract", lambda search_text, profile: candidates)
    monkeypatch.setattr(roles_mod, "_score_one", lambda candidate, profile: _strong_score())

    out = roles_mod.roles_node({"profile": valid_profile.model_dump()})

    assert "scored" in out
    assert len(out["scored"]) == 2
    assert out["scored"][0]["list_position"] == 0
    assert out["scored"][0]["raw_text"] == "ACME | Backend Engineer"
    assert out["scored"][0]["label"] == "strong"
    assert out["scored"][0]["total"] == 4.0


def test_roles_caps_candidates_at_max(monkeypatch, valid_profile):
    # _extract returns more than SCORE_MAX_CANDIDATES; node should slice to the cap
    candidates = [
        Candidate(list_position=i, raw_text=f"posting {i}", required_skills=[])
        for i in range(SCORE_MAX_CANDIDATES + 3)
    ]
    monkeypatch.setattr(roles_mod, "_find", lambda profile: "search results text")
    monkeypatch.setattr(roles_mod, "_extract", lambda search_text, profile: candidates)
    monkeypatch.setattr(roles_mod, "_score_one", lambda candidate, profile: _strong_score())

    out = roles_mod.roles_node({"profile": valid_profile.model_dump()})

    assert len(out["scored"]) == SCORE_MAX_CANDIDATES
