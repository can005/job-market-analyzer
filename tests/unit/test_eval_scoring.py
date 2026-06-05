"""Scoring-eval tests. Production scorer mocked via an injected callable."""

from evals.scoring import evaluate_scoring


def _case(cid: str, expected: str, hint: str | None = None) -> dict:
    return {
        "id": cid,
        "profile": {},
        "candidate": {"hint": hint} if hint else {},
        "expected_band": expected,
    }


def _scorer_by_hint(mapping: dict[str | None, tuple[str, float]]):
    def score(profile: dict, candidate: dict) -> dict:
        label, total = mapping[candidate.get("hint")]
        return {"label": label, "total": total}

    return score


def test_perfect_predictor_yields_full_accuracy():
    cases = [_case("S1", "strong", "a"), _case("S2", "moderate", "b")]
    scorer = _scorer_by_hint({"a": ("strong", 4.5), "b": ("moderate", 3.0)})

    out = evaluate_scoring(cases, scorer)

    assert out["summary"]["accuracy"] == 1.0
    assert out["summary"]["n_cases"] == 2
    assert all(c["correct"] for c in out["per_case"])


def test_mixed_predictions_yield_partial_accuracy():
    cases = [
        _case("S1", "strong", "a"),
        _case("S2", "weak", "b"),
        _case("S3", "moderate", "c"),
    ]
    scorer = _scorer_by_hint({"a": ("strong", 4.5), "b": ("strong", 4.0), "c": ("moderate", 3.0)})

    out = evaluate_scoring(cases, scorer)

    assert out["summary"]["accuracy"] == 2 / 3
    correct_ids = {c["id"] for c in out["per_case"] if c["correct"]}
    assert correct_ids == {"S1", "S3"}


def test_per_case_carries_predicted_total():
    cases = [_case("S1", "strong", "a")]
    scorer = _scorer_by_hint({"a": ("weak", 1.25)})

    out = evaluate_scoring(cases, scorer)

    assert out["per_case"][0]["predicted_total"] == 1.25
    assert out["per_case"][0]["predicted_band"] == "weak"
    assert out["per_case"][0]["correct"] is False


def test_empty_cases_yields_zero_accuracy():
    out = evaluate_scoring([], lambda *_: None)
    assert out == {"summary": {"n_cases": 0, "accuracy": 0.0}, "per_case": []}
