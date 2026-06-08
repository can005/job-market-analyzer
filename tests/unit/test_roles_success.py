"""roles_node happy path with LLM helpers stubbed.

Asserts the worker assembles _find → _extract → _score_batch → _classify into the
expected `scored` shape, skips postings already seen in earlier passes, and picks
the broadening rung from the pass count."""

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
        Candidate(hn_id=0, raw_text="ACME | Backend Engineer", required_skills=[]),
        Candidate(hn_id=1, raw_text="WidgetCo | Python dev", required_skills=[]),
    ]
    monkeypatch.setattr(roles_mod, "_find", lambda profile, directive=None: "search results text")
    monkeypatch.setattr(roles_mod, "_extract", lambda search_text, profile: candidates)
    monkeypatch.setattr(
        roles_mod, "_score_batch", lambda cands, profile: [_strong_score() for _ in cands]
    )

    out = roles_mod.roles_node({"profile": valid_profile.model_dump()})

    assert len(out["scored"]) == 2
    assert out["scored"][0]["hn_id"] == 0
    assert out["scored"][0]["raw_text"] == "ACME | Backend Engineer"
    assert out["scored"][0]["label"] == "strong"
    assert out["scored"][0]["total"] == 4.0
    assert [c["hn_id"] for c in out["candidates"]] == [0, 1]
    assert out["refine_passes"] == 1


def test_roles_caps_candidates_at_max(monkeypatch, valid_profile):
    candidates = [
        Candidate(hn_id=i, raw_text=f"posting {i}", required_skills=[])
        for i in range(SCORE_MAX_CANDIDATES + 3)
    ]
    monkeypatch.setattr(roles_mod, "_find", lambda profile, directive=None: "search results text")
    monkeypatch.setattr(roles_mod, "_extract", lambda search_text, profile: candidates)
    monkeypatch.setattr(
        roles_mod, "_score_batch", lambda cands, profile: [_strong_score() for _ in cands]
    )

    out = roles_mod.roles_node({"profile": valid_profile.model_dump()})

    assert len(out["scored"]) == SCORE_MAX_CANDIDATES


def test_roles_scores_only_postings_not_yet_seen(monkeypatch, valid_profile):
    extracted = [
        Candidate(hn_id=0, raw_text="already scored last pass", required_skills=[]),
        Candidate(hn_id=7, raw_text="surfaced by broadening", required_skills=[]),
    ]
    scored_ids = {}

    def fake_batch(cands, profile):
        scored_ids["seen"] = [c.hn_id for c in cands]
        return [_strong_score() for _ in cands]

    monkeypatch.setattr(roles_mod, "_find", lambda profile, directive=None: "text")
    monkeypatch.setattr(roles_mod, "_extract", lambda search_text, profile: extracted)
    monkeypatch.setattr(roles_mod, "_score_batch", fake_batch)

    out = roles_mod.roles_node(
        {
            "profile": valid_profile.model_dump(),
            "refine_passes": 1,
            "candidates": [{"hn_id": 0}],
        }
    )

    assert scored_ids["seen"] == [7]
    assert [s["hn_id"] for s in out["scored"]] == [7]
    assert [c["hn_id"] for c in out["candidates"]] == [7]


def test_ladder_directive_climbs_with_pass_count():
    assert roles_mod._ladder_directive(0) is None
    assert roles_mod._ladder_directive(1) == roles_mod.BROADENING_LADDER[0]
    assert roles_mod._ladder_directive(2) == roles_mod.BROADENING_LADDER[1]
    assert roles_mod._ladder_directive(99) == roles_mod.BROADENING_LADDER[-1]
