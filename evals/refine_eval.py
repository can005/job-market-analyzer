"""Refinement-loop eval: strong-candidate yield from pass 0 alone vs the full
broadened loop, per profile. Drives the real roles_node and termination policy
against live LLM + retrieval calls, capturing pass 0 as the baseline inside a
single loop run (one loop per profile, not two). Run with:

    python -m evals.refine_eval
"""

import json
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

import agents.tools as tools_mod
from agents.roles import roles_node
from agents.state import merge_by_hn_id
from agents.supervisor import ROLES, _roles_should_run
from core.config import (
    EVAL_RESULTS_DATA_DIR,
    HN_JOB_POSTING_EVAL_TABLE_NAME,
    OPENAI_EMBEDDING_MODEL,
)
from ingestion.db import get_connection_string


def _eval_vectorstore() -> PGVector:
    return PGVector(
        embeddings=OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL),
        connection=get_connection_string(),
        collection_name=HN_JOB_POSTING_EVAL_TABLE_NAME,
    )


PROFILES = [
    {
        "skills": [{"skill": "Rust", "years": 6}, {"skill": "embedded systems", "years": 5}],
        "domain": "embedded firmware for robotics",
        "logistics": "onsite only, Berlin",
    },
    {
        "skills": [{"skill": "Python", "years": 8}, {"skill": "React", "years": 5}],
        "domain": "full-stack web product",
        "logistics": "remote, US",
    },
    {
        "skills": [{"skill": "Haskell", "years": 4}, {"skill": "type theory", "years": 3}],
        "domain": "compiler and programming-language tooling",
        "logistics": "remote, EU",
    },
]


def _tally(scored: list[dict]) -> dict:
    bands = {"strong": 0, "moderate": 0, "weak": 0}
    for s in scored:
        bands[s["label"]] += 1
    mean_total = round(sum(s["total"] for s in scored) / len(scored), 2) if scored else 0.0
    return {"n": len(scored), **bands, "mean_total": mean_total}


def _relevant(tally: dict) -> int:
    return tally["strong"] + tally["moderate"]


def run_loop(profile: dict) -> list[dict]:
    state = {
        "profile": profile,
        "plan": ["scored"],
        "candidates": [],
        "scored": [],
        "refine_passes": 0,
    }
    snapshots = []
    while _roles_should_run(state):
        out = roles_node(state)
        if out.get("worker_status", {}).get(ROLES) == "failed":
            break
        state["candidates"] = merge_by_hn_id(state["candidates"], out.get("candidates", []))
        state["scored"] = merge_by_hn_id(state["scored"], out.get("scored", []))
        state["refine_passes"] += out.get("refine_passes", 0)
        snapshots.append(_tally(state["scored"]))
    return snapshots


PAUSE_BETWEEN_PROFILES_S = 10


def main() -> None:
    load_dotenv()
    tools_mod.get_vectorstore = _eval_vectorstore
    results = []
    for i, profile in enumerate(PROFILES):
        if i:
            time.sleep(PAUSE_BETWEEN_PROFILES_S)
        snapshots = run_loop(profile)
        results.append({"profile": profile, "snapshots": snapshots})

        label = f"{profile['domain']} | {profile['logistics']}"
        if not snapshots:
            print(f"{label}\n  roles worker failed (transient)\n")
            continue
        baseline, final = snapshots[0], snapshots[-1]
        print(label)
        print(f"  pass 0 (baseline):     {baseline}")
        print(f"  full loop ({len(snapshots)} pass{'es' if len(snapshots) > 1 else ' '}): {final}")
        print(
            f"  delta  strong {final['strong'] - baseline['strong']:+d}   "
            f"relevant {_relevant(final) - _relevant(baseline):+d}\n"
        )

    out_dir = Path(EVAL_RESULTS_DATA_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "refine_eval.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
