"""Benchmark scoring fan-out: sequential `_score_one` vs batched `_score_batch`.

Times wall-clock per iteration over N real corpus postings against live LLM
calls — costs roughly one scoring run per iteration per path. Run with:

    python -m evals.benchmark
"""

import json
import time
from pathlib import Path
from statistics import mean, quantiles

from dotenv import load_dotenv

from agents.roles import _score_batch, _score_one
from core.config import OPENAI_CHAT_MODEL
from core.schemas import Candidate

CORPUS_PATH = Path("tests/fixtures/eval/hn_corpus.json")
PROFILE = {
    "skills": [
        {"skill": "Python", "years": 7},
        {"skill": "FastAPI", "years": 4},
        {"skill": "TypeScript", "years": 3},
    ],
    "domain": "backend product engineering for healthcare workflows",
    "logistics": "remote, US",
}
N_CANDIDATES = 5
ITERATIONS = 3


def _build_candidates(n: int) -> list[Candidate]:
    corpus = json.loads(CORPUS_PATH.read_text())[:n]
    return [Candidate(hn_id=p["id"], raw_text=p["text"], required_skills=[]) for p in corpus]


def _time(fn, iterations: int) -> list[float]:
    times = []
    for _ in range(iterations):
        t = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t)
    return times


def _summary(times: list[float]) -> dict:
    q = quantiles(times, n=20) if len(times) >= 2 else None
    return {
        "mean": round(mean(times), 2),
        "p50": round(q[9], 2) if q else round(times[0], 2),
        "p95": round(q[18], 2) if q else round(max(times), 2),
        "raw": [round(t, 2) for t in times],
    }


def main() -> None:
    load_dotenv()
    candidates = _build_candidates(N_CANDIDATES)
    print(f"Scorer: {OPENAI_CHAT_MODEL} | N={N_CANDIDATES} candidates × {ITERATIONS} iterations\n")

    seq = _time(lambda: [_score_one(c, PROFILE) for c in candidates], ITERATIONS)
    bat = _time(lambda: _score_batch(candidates, PROFILE), ITERATIONS)

    print(f"sequential: {_summary(seq)}")
    print(f"batched:    {_summary(bat)}")

    if mean(bat) > 0:
        print(f"\nspeedup (mean seq / mean batched): {mean(seq) / mean(bat):.2f}×")


if __name__ == "__main__":
    main()
