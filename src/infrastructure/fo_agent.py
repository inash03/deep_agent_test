"""LangGraph ReAct FoAgent for Front-Office STP triage.

Graph topology:

  START
    │
    ▼
  [agent_node] ◄─────────────────────────────────────────┐
    │                                                     │
    │ _route_after_agent                                  │
    ├─ create_amend_event  ──► [create_amend_event_node]  │ ← interrupt_before
    ├─ create_cancel_event ──► [create_cancel_event_node] │ ← interrupt_before
    ├─ other tool calls    ──► [read_tools_node]         ─┘
    └─ no tool calls       ──► END

HITL flow:
  - Graph pauses before any node in _FO_HITL_TOOL_TO_NODE
  - Caller checks get_state().next to identify which node is pending
  - On approval : graph.invoke(None, config)
  - On rejection: graph.update_state() injects rejection ToolMessage,
                  then graph.invoke(None, config) → back to agent_node
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from src.infrastructure.tools import (
    FO_ALL_TOOLS,
    FO_READ_ONLY_TOOLS,
    create_amend_event,
    create_cancel_event,
)

# Maps each HITL tool name → the graph node that executes it
_FO_HITL_TOOL_TO_NODE: dict[str, str] = {
    "create_amend_event": "create_amend_event_node",
    "create_cancel_event": "create_cancel_event_node",
}

_logger = logging.getLogger("stp_triage.fo_agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

FO_SYSTEM_PROMPT = """\
You are a Front-Office (FO) STP exception triage agent at a securities firm.
Your job is to investigate FoCheck failures for a trade, correct trade data
errors where possible, and handle BO-sent-back trades by amending, cancelling,
providing an explanation, or escalating to a FO User.

=== INVESTIGATION STEPS (follow in order) ===

1. Call get_fo_check_results(trade_id) to retrieve FoCheck rule results.
   - Note: the response includes workflow_status and sendback_count.
   - If sendback_count >= 1, the trade was sent back by BoAgent.
     Call get_bo_sendback_reason(trade_id) to read BO's concern before deciding.

2. Call get_trade_detail(trade_id) for full trade context
   (value_date, trade_date, instrument, amount, currencies).

3. For each FAILED FoCheck rule, investigate:
   - trade_date_not_future:
     → Trade date is in the future — likely a data entry error.
   - trade_date_not_weekend:
     → Trade was booked on a weekend — needs date correction.
   - value_date_after_trade_date:
     → Value date is before trade date — FO input error.
   - value_date_not_past:
     → Value date is in the past — missed settlement window; may need cancel.
   - value_date_settlement_cycle (WARNING only):
     → Value date may not satisfy T+2 convention.
       This is sometimes legitimate (special settlement). Investigate.
   - amount_positive:
     → Amount is zero or negative — FO data entry error; needs amendment.
   - settlement_currency_consistency:
     → Settlement currency differs from instrument currency — needs correction.

4. For BO sendback (sendback_count >= 1):
   - Read bo_sendback_reason carefully.
   - Determine if the issue is genuinely FO-side (requires amendment/cancel)
     or BO-side (SSI/counterparty problem that FO can explain away).

=== CORRECTIVE ACTIONS (call tools — do not just recommend) ===

A. Trade data errors that can be corrected (wrong date, amount, currency):
   → MUST call create_amend_event(trade_id, reason, amended_fields).
     amended_fields must be a JSON string with only the fields to change.
     Example: '{"value_date": "2026-05-01"}' or '{"amount": "500000.00"}'.
     Operator will approve.

B. Trade is fundamentally wrong and should not settle
   (e.g. counterparty deal was cancelled, instrument delisted):
   → MUST call create_cancel_event(trade_id, reason).
     Operator will approve. Explain precisely why settlement cannot proceed.

C. BO sent back but trade data IS correct
   (BO's concern is about SSI/counterparty, not FO trade content):
   → MUST call provide_explanation(trade_id, explanation).
     Explain why the trade data is correct and what BO should resolve on its side.
     This transitions the trade back to FoValidated so BoAgent can retry.

D. Cannot determine the fix / ambiguous situation / requires senior judgment:
   → MUST call escalate_to_fo_user(trade_id, reason).
     Describe the specific uncertainty or complexity that requires human review.

=== OUTPUT FORMAT ===

After all investigation and action tool calls, output a raw JSON object (no markdown):

{"diagnosis": "<findings>", "root_cause": "<MISSING_SSI|BIC_FORMAT_ERROR|IBAN_FORMAT_ERROR|COUNTERPARTY_NOT_FOUND|INVALID_VALUE_DATE|INSTRUMENT_NOT_FOUND|SWIFT_AC01|SWIFT_AG01|COMPOUND_FAILURE|UNKNOWN>", "recommended_action": "<next steps>"}
"""

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class FoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_agent(state: FoAgentState) -> str:
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return END
    # Once a HITL action has been approved and executed, prevent re-entering
    # any HITL node (LLM may try to call the same tool again after approval).
    if state.get("action_taken", False):
        return END
    for tc in last.tool_calls:
        if tc["name"] in _FO_HITL_TOOL_TO_NODE:
            return _FO_HITL_TOOL_TO_NODE[tc["name"]]
    return "read_tools"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_fo_graph() -> Any:
    """Build and compile the FoAgent LangGraph.

    Returns a compiled StateGraph with MemorySaver checkpointer and
    interrupt_before on all HITL nodes.
    """
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    ).bind_tools(FO_ALL_TOOLS)

    read_tools_node = ToolNode(FO_READ_ONLY_TOOLS)

    def agent_node(state: FoAgentState) -> dict[str, Any]:
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=FO_SYSTEM_PROMPT)] + messages
        _logger.info(
            "fo_agent_node: invoking LLM",
            extra={"node": "agent", "trade_id": state.get("trade_id"), "message_count": len(messages)},
        )
        response = llm.invoke(messages)
        if response.tool_calls:
            for tc in response.tool_calls:
                _logger.info(
                    "fo_agent_node: tool call planned",
                    extra={"node": "agent", "tool": tc["name"], "tool_args": tc["args"]},
                )
        else:
            _logger.info(
                "fo_agent_node: final response",
                extra={"node": "agent", "trade_id": state.get("trade_id")},
            )
        return {"messages": [response]}

    def _make_hitl_node(tool_name: str, tool_fn: Any) -> Any:
        def node(state: FoAgentState) -> dict[str, Any]:
            last = state["messages"][-1]
            tool_call = next(tc for tc in last.tool_calls if tc["name"] == tool_name)
            _logger.info(
                f"{tool_name}_node: executing (HITL approved)",
                extra={"node": f"{tool_name}_node", "trade_id": state.get("trade_id"),
                       "tool_args": tool_call["args"]},
            )
            try:
                result = tool_fn.invoke(tool_call["args"])
            except Exception as exc:
                _logger.error(
                    "%s_node: tool execution failed: %s", tool_name, exc, exc_info=True
                )
                result = json.dumps({"success": False, "error": f"{type(exc).__name__}: {exc}"})
            return {
                "messages": [ToolMessage(content=result, tool_call_id=tool_call["id"])],
                "action_taken": True,
            }
        return node

    create_amend_event_node = _make_hitl_node("create_amend_event", create_amend_event)
    create_cancel_event_node = _make_hitl_node("create_cancel_event", create_cancel_event)

    hitl_node_names = list(_FO_HITL_TOOL_TO_NODE.values())

    builder = StateGraph(FoAgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("read_tools", read_tools_node)
    builder.add_node("create_amend_event_node", create_amend_event_node)
    builder.add_node("create_cancel_event_node", create_cancel_event_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        _route_after_agent,
        {**{n: n for n in hitl_node_names}, "read_tools": "read_tools", END: END},
    )
    builder.add_edge("read_tools", "agent")
    for node_name in hitl_node_names:
        builder.add_edge(node_name, "agent")

    from src.infrastructure.db.checkpointer import get_checkpointer
    return builder.compile(
        checkpointer=get_checkpointer(),
        interrupt_before=hitl_node_names,
    )
