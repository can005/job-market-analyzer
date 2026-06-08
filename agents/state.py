import operator
from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


def merge_by_hn_id(existing: list[dict], new: list[dict]) -> list[dict]:
    """Accumulate roles output across refinement passes, dedup by HN id, first write wins."""
    by_id = {item["hn_id"]: item for item in existing or []}
    for item in new:
        by_id.setdefault(item["hn_id"], item)
    return list(by_id.values())


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # user-facing channel; can accumulate → reducer
    profile: NotRequired[dict]  # single-owner, set at entry
    question: NotRequired[str]  # single-owner, set at seam
    plan: NotRequired[list[str]]  # single-owner, set at entry
    candidates: Annotated[list[dict], merge_by_hn_id]  # accumulate across passes, dedup by id
    scored: Annotated[list[dict], merge_by_hn_id]  # score-only-new accumulates, dedup by id
    market_findings: NotRequired[list[dict]]  # write-once → default LastValue channel
    refine_passes: Annotated[int, operator.add]  # roles re-dispatch counter; count-cap guard
    worker_status: NotRequired[dict[str, str]]  # sparse failure markers; absent = ok or not run
    worker_errors: NotRequired[dict[str, str]]  # reason per failed worker (transient error type)
