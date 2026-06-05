"""Retrieval eval — hit@k and MRR against gold HN ids.

The retriever is injected as a callable (question, k) -> list[int], keeping the
metric math pure and IO-free for unit testing. Production wiring builds the
retriever from a PGVector collection in the orchestration entry point."""

from typing import Callable

from core.config import OPENAI_EMBEDDING_MODEL

Retriever = Callable[[str, int], list[int]]


def _reciprocal_rank(retrieved: list[int], gold: set[int]) -> float:
    for rank, hit_id in enumerate(retrieved, start=1):
        if hit_id in gold:
            return 1.0 / rank
    return 0.0


def evaluate_retrieval(questions: list[dict], retriever: Retriever, k: int = 25) -> dict:
    per_question = []
    for q in questions:
        retrieved = retriever(q["question"], k)
        if q["type"] == "distractor":
            per_question.append(
                {
                    "id": q["id"],
                    "type": q["type"],
                    "retrieved": retrieved,
                    "scoring_excluded": True,
                }
            )
            continue
        gold = set(q["gold_ids"])
        hit = any(rid in gold for rid in retrieved)
        rr = _reciprocal_rank(retrieved, gold)
        per_question.append(
            {
                "id": q["id"],
                "type": q["type"],
                "gold_ids": q["gold_ids"],
                "retrieved": retrieved,
                "hit": hit,
                "rr": rr,
            }
        )

    scored = [r for r in per_question if not r.get("scoring_excluded")]
    n_scored = len(scored)
    hit_rate = sum(r["hit"] for r in scored) / n_scored if n_scored else 0.0
    mrr = sum(r["rr"] for r in scored) / n_scored if n_scored else 0.0

    summary = {
        "k": k,
        "embedding_model": OPENAI_EMBEDDING_MODEL,
        "n_scored": n_scored,
        "n_distractors_excluded": len(per_question) - n_scored,
        f"hit_at_{k}": hit_rate,
        "mrr": mrr,
    }
    return {"summary": summary, "per_question": per_question}
