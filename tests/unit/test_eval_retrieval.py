"""Retrieval-eval metric tests. Vectorstore mocked via an injected retriever."""

from evals.retrieval import evaluate_retrieval


def _q(qid, qtype, gold, abstain=False):
    return {
        "id": qid,
        "question": qid.lower(),
        "type": qtype,
        "gold_ids": gold,
        "expected_abstain": abstain,
    }


def _retriever(mapping: dict[str, list[int]]):
    def retrieve(question: str, k: int) -> list[int]:
        return mapping.get(question, [])[:k]

    return retrieve


def test_hit_at_k_and_mrr_basic():
    questions = [_q("Q1", "single_fact", [1]), _q("Q2", "single_fact", [2])]
    retriever = _retriever({"q1": [1, 99, 98], "q2": [99, 98, 2, 97]})

    out = evaluate_retrieval(questions, retriever, k=10)

    assert out["summary"]["hit_at_10"] == 1.0
    assert out["summary"]["mrr"] == (1.0 + 1 / 3) / 2


def test_miss_contributes_zero_mrr():
    questions = [_q("Q1", "single_fact", [1])]
    retriever = _retriever({"q1": [99, 98]})

    out = evaluate_retrieval(questions, retriever, k=10)

    assert out["summary"]["hit_at_10"] == 0.0
    assert out["summary"]["mrr"] == 0.0


def test_distractor_excluded_from_summary():
    questions = [
        _q("Q1", "single_fact", [1]),
        _q("Q2", "distractor", [], abstain=True),
    ]
    retriever = _retriever({"q1": [1], "q2": [99]})

    out = evaluate_retrieval(questions, retriever, k=10)

    assert out["summary"]["n_scored"] == 1
    assert out["summary"]["n_distractors_excluded"] == 1
    assert out["summary"]["hit_at_10"] == 1.0


def test_multi_hop_first_hit_drives_mrr():
    questions = [_q("Q1", "multi_hop", [1, 2])]
    retriever = _retriever({"q1": [99, 2, 1]})

    out = evaluate_retrieval(questions, retriever, k=10)

    assert out["per_question"][0]["rr"] == 1 / 2
