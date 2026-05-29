"""collect_tool_output: join ToolMessage content only — never the agent's prose
(AIMessage) or the user turn (HumanMessage). Pure function."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agents.tools import collect_tool_output


def test_keeps_only_tool_messages():
    result = {
        "messages": [
            HumanMessage("the question"),
            ToolMessage(content="rows A", tool_call_id="1"),
            AIMessage("here is my summary"),
            ToolMessage(content="rows B", tool_call_id="2"),
        ]
    }
    assert collect_tool_output(result) == "rows A\n\nrows B"


def test_no_tool_messages_returns_empty():
    result = {"messages": [HumanMessage("q"), AIMessage("just prose")]}
    assert collect_tool_output(result) == ""


def test_single_tool_message():
    result = {"messages": [ToolMessage(content="only rows", tool_call_id="1")]}
    assert collect_tool_output(result) == "only rows"
