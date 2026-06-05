"""Scoring eval — deterministic floor: predicted band vs expected band.

The scorer is injected as a callable (profile, candidate) -> classified dict
(the shape `_classify` returns: includes `label` and `total`). This keeps the
metric layer pure; the orchestration entry wires the production scoring path
(`_score_one` + `_classify`) into the scorer at runtime."""

from typing import Callable

Scorer = Callable[[dict, dict], dict]


def evaluate_scoring(cases: list[dict], scorer: Scorer) -> dict:
    per_case = []
    for case in cases:
        predicted = scorer(case["profile"], case["candidate"])
        correct = predicted["label"] == case["expected_band"]
        per_case.append(
            {
                "id": case["id"],
                "expected_band": case["expected_band"],
                "predicted_band": predicted["label"],
                "predicted_total": predicted["total"],
                "correct": correct,
            }
        )

    n = len(per_case)
    accuracy = sum(c["correct"] for c in per_case) / n if n else 0.0
    return {
        "summary": {"n_cases": n, "accuracy": accuracy},
        "per_case": per_case,
    }
