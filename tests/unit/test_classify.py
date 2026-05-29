"""_classify: averages the seniority list, weighted sum, band lookup.
Pure function — no external dep. Band floors: 4.0 strong, 2.5 moderate, 0.0 weak."""

from agents.roles import _classify
from core.schemas import Candidate, ScoreSchema, SkillSeniorityScore


def _candidate():
    return Candidate(list_position=0, raw_text="posting text", required_skills=[])


def _score(skills, seniority_scores, domain, logistics):
    return ScoreSchema(
        skills_match=skills,
        seniority_match=[SkillSeniorityScore(skill="s", score=v) for v in seniority_scores],
        domain_match=domain,
        logistics_match=logistics,
        reasoning="test",
    )


def test_seniority_list_is_averaged():
    # avg(2, 4) = 3.0 lands in seniority_match of the output dict
    out = _classify(_candidate(), _score(0, [2, 4], 0, 0))
    assert out["seniority_match"] == 3.0


def test_empty_seniority_scores_to_zero():
    # no required_skills → no seniority entries → contributes 0, no ZeroDivision
    out = _classify(_candidate(), _score(5, [], 5, 5))
    assert out["seniority_match"] == 0
    # 0.40*5 + 0.25*0 + 0.20*5 + 0.15*5 = 3.75
    assert out["total"] == 3.75
    assert out["label"] == "moderate"


def test_band_strong_at_exactly_4():
    # all dims 4 → weights sum to 1.0 → total 4.0 → strong (floor is inclusive)
    out = _classify(_candidate(), _score(4, [4], 4, 4))
    assert out["total"] == 4.0
    assert out["label"] == "strong"


def test_band_moderate_at_exactly_2_5():
    # 0.40*2 + 0.25*4 + 0.20*2 + 0.15*2 = 2.5 → moderate (inclusive floor)
    out = _classify(_candidate(), _score(2, [4], 2, 2))
    assert out["total"] == 2.5
    assert out["label"] == "moderate"


def test_band_weak_below_2_5():
    # all dims 2 → 2.0 → weak
    out = _classify(_candidate(), _score(2, [2], 2, 2))
    assert out["total"] == 2.0
    assert out["label"] == "weak"


def test_passthrough_fields():
    c = Candidate(list_position=7, raw_text="ACME | Backend Engineer", required_skills=[])
    out = _classify(c, _score(3, [3], 3, 3))
    assert out["list_position"] == 7
    assert out["raw_text"] == "ACME | Backend Engineer"
    assert out["reasoning"] == "test"
