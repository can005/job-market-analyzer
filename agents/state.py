from typing import Annotated, NotRequired, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # user-facing channel; can accumulate → reducer
    profile: NotRequired[dict]                # single-owner, set at entry
    plan: NotRequired[list[str]]              # single-owner, set at entry
    candidates: NotRequired[list[dict]]       # write-once → default LastValue channel
    scored: NotRequired[list[dict]]           # write-once → default LastValue channel
    market_findings: NotRequired[list[dict]]  # write-once → default LastValue channel