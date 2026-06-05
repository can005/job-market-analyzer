"""Reasoning-eval tests. Judge_fn mocked; scorer mocked."""

from evals.reasoning import evaluate_reasoning


def _case(cid: str) -> dict:
    return {
        "id": cid,
        "profile": {"domain": "backend"},
        "candidate": {"hn_id": 1, "raw_text": "posting text"},
        "expected_band": "moderate",
    }


def _scorer_returning(reasoning: str):
    def score(profile, candidate):
        return {"label": "strong", "total": 4.0, "reasoning": reasoning}

    return score


def _fixed_judge(rubric: float, evidence: float, notes: str = "ok"):
    def judge(profile, posting, rationale):
        return {"rubric_match": rubric, "evidence_grounded": evidence, "notes": notes}

    return judge


def test_judge_skipped_when_judge_fn_none(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    out = evaluate_reasoning([_case("S1")], _scorer_returning("r"), judge_fn=None)
    assert out["summary"]["judge_skipped"] is True
    assert out["summary"]["judge_model"] == "gpt-4o"
    assert out["per_case"] == []


def test_aggregates_judge_scores(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    cases = [_case("S1"), _case("S2")]
    out = evaluate_reasoning(cases, _scorer_returning("r"), _fixed_judge(0.8, 1.0))
    assert out["summary"]["mean_rubric_match"] == 0.8
    assert out["summary"]["mean_evidence_grounded"] == 1.0
    assert out["summary"]["n_cases"] == 2
    assert out["summary"]["judge_skipped"] is False


def test_per_case_includes_assessment_fields(monkeypatch):
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    out = evaluate_reasoning(
        [_case("S1")], _scorer_returning("r"), _fixed_judge(0.5, 0.6, "specific")
    )
    assert out["per_case"][0] == {
        "id": "S1",
        "rubric_match": 0.5,
        "evidence_grounded": 0.6,
        "notes": "specific",
    }
