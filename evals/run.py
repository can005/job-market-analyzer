"""End-to-end eval orchestration: re-embed the frozen corpus (cache-aware),
run retrieval, deterministic scoring, and reasoning-quality evals, and write a
single JSON output with metadata + per-case results.

Invoked as `python -m evals.run`. Idempotent corpus embedding: a sentinel records
`(corpus_hash, embedding_model)` and re-embedding is skipped when both match."""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from agents.roles import _classify, _score_one
from core.config import (
    EVAL_RESULTS_DATA_DIR,
    HN_JOB_POSTING_EVAL_TABLE_NAME,
    OPENAI_EMBEDDING_MODEL,
)
from core.logging import setup_logging
from core.schemas import Candidate
from evals.judge import get_judge, judge_metadata
from evals.reasoning import build_judge_fn, evaluate_reasoning
from evals.retrieval import evaluate_retrieval
from evals.scoring import evaluate_scoring
from ingestion.db import get_connection_string
from ingestion.hn_embed import embed_postings

CORPUS_PATH = Path("tests/fixtures/eval/hn_corpus.json")
QUESTIONS_PATH = Path("tests/fixtures/eval/questions.json")
SCORING_CASES_PATH = Path("tests/fixtures/eval/scoring_cases.json")
CACHE_DIR = Path("data/eval/cache")
SENTINEL_PATH = CACHE_DIR / "embed_sentinel.json"
RESULTS_DIR = Path(EVAL_RESULTS_DATA_DIR)

logger = logging.getLogger(__name__)


def _corpus_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _embed_if_needed(corpus_hash: str) -> bool:
    if SENTINEL_PATH.exists():
        prior = json.loads(SENTINEL_PATH.read_text())
        if prior == {"corpus_hash": corpus_hash, "embedding_model": OPENAI_EMBEDDING_MODEL}:
            logger.info("eval.embed.skipped", extra={"reason": "cache_hit"})
            return False
    logger.info("eval.embed.start", extra={"collection": HN_JOB_POSTING_EVAL_TABLE_NAME})
    embed_postings(source=str(CORPUS_PATH), collection=HN_JOB_POSTING_EVAL_TABLE_NAME)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SENTINEL_PATH.write_text(
        json.dumps({"corpus_hash": corpus_hash, "embedding_model": OPENAI_EMBEDDING_MODEL})
    )
    return True


def _build_retriever():
    vs = PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name=HN_JOB_POSTING_EVAL_TABLE_NAME,
    )

    def retrieve(question: str, k: int) -> list[int]:
        return [doc.metadata["id"] for doc in vs.similarity_search(question, k=k)]

    return retrieve


class _MemoScorer:
    """Memoize per-case scorer calls so the deterministic floor and reasoning
    layer share one LLM call per case instead of doubling cost."""

    def __init__(self) -> None:
        self._cache: dict = {}

    def __call__(self, profile: dict, candidate_dict: dict) -> dict:
        key = (json.dumps(profile, sort_keys=True), candidate_dict.get("hn_id"))
        if key not in self._cache:
            candidate = Candidate(**candidate_dict)
            score = _score_one(candidate, profile)
            self._cache[key] = _classify(candidate, score)
        return self._cache[key]


def main() -> None:
    setup_logging()
    load_dotenv()

    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    corpus_hash = _corpus_hash(CORPUS_PATH)
    questions = json.loads(QUESTIONS_PATH.read_text())
    scoring_cases = (
        json.loads(SCORING_CASES_PATH.read_text()) if SCORING_CASES_PATH.exists() else []
    )

    _embed_if_needed(corpus_hash)
    retriever = _build_retriever()
    retrieval_result = evaluate_retrieval(questions, retriever, k=25)

    scoring_result = None
    reasoning_result = None
    if scoring_cases:
        scorer = _MemoScorer()
        scoring_result = evaluate_scoring(scoring_cases, scorer)
        judge = get_judge()
        judge_fn = build_judge_fn(judge) if judge is not None else None
        reasoning_result = evaluate_reasoning(scoring_cases, scorer, judge_fn)

    ended_at = datetime.now(timezone.utc)
    output = {
        "metadata": {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "embedding_model": OPENAI_EMBEDDING_MODEL,
            "corpus_hash": corpus_hash,
            "n_questions": len(questions),
            "n_scoring_cases": len(scoring_cases),
            **judge_metadata(),
        },
        "retrieval": retrieval_result,
        "scoring": scoring_result,
        "reasoning": reasoning_result,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"eval_{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(output, indent=2))
    logger.info("eval.done", extra={"output_path": str(out_path), "run_id": run_id})


if __name__ == "__main__":
    main()
