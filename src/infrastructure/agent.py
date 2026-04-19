"""LangGraph ReAct agent for STP Exception Triage.

Graph topology:

  START
    │
    ▼
  [agent_node] ◄────────────────────────┐
    │                                   │
    │ route_after_agent                 │
    ├─ register_ssi tool call ──► [register_ssi_node]  ← interrupt_before here
    ├─ other tool calls ─────────► [read_tools_node]   ─┘
    └─ no tool calls ────────────► END

HITL flow:
  - Graph pauses before register_ssi_node
  - Caller checks get_state().next == ("register_ssi_node",)
  - On approval : graph.invoke(None, config)  → continues normally
  - On rejection: graph.update_state() injects a rejection ToolMessage,
                  then graph.invoke(None, config) continues to agent_node
"""

from __future__ import annotations

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
    ALL_TOOLS,
    READ_ONLY_TOOLS,
    escalate,
    reactivate_counterparty,
    register_ssi,
    update_ssi,
)

# Maps each HITL tool name → the graph node that executes it
_HITL_TOOL_TO_NODE: dict[str, str] = {
    "register_ssi": "register_ssi_node",
    "reactivate_counterparty": "reactivate_counterparty_node",
    "update_ssi": "update_ssi_node",
    "escalate": "escalate_node",
}

_logger = logging.getLogger("stp_triage.agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert STP (Straight-Through Processing) exception triage agent
at a securities firm. Your job is to investigate a failed trade and diagnose
the root cause using the tools available to you, then take corrective action
where possible.

=== INVESTIGATION STEPS (follow in order, do not skip) ===

1. Call get_trade_detail to retrieve the trade.
2. Call get_counterparty to verify the counterparty LEI.
   - Check the is_active field. If is_active is false, the counterparty is
     blocked from trading (SWIFT code AG01).
3. Call get_counterparty_exception_history for the counterparty LEI.
   - If the result contains a "warning" field (3 or more failures in 30 days),
     include that warning verbatim in your diagnosis.
4. Call get_triage_history for the trade ID.
   - If a past COMPLETED triage exists with the same root_cause, incorporate
     its recommended_action (prefix with "Previously resolved by: ...").
5. Call get_reference_data to verify the instrument.
6. Call get_settlement_instructions to check if an SSI is registered.
   - IBAN validation: must match [A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}
     (e.g. GB29NWBK60161331926819). Patterns like "GBXX-INVALID-*" are malformed.
   - BIC validation: must be exactly 8 or 11 characters. An 11-character BIC
     ending in "XXX" denotes a head-office code that may not be actively routed.

=== CORRECTIVE ACTIONS (call tools — do not just recommend, actually call them) ===

After completing the investigation, you MUST call the appropriate tool:

A. Counterparty inactive (is_active = false):
   → MUST call reactivate_counterparty(lei).
   → An operator will review before the change takes effect.

B. No internal SSI found:
   → MUST call lookup_external_ssi(lei, currency).
   → If lookup returns data: MUST call register_ssi(...) with those exact values.
   → If lookup returns nothing: set root_cause=MISSING_SSI, call
     escalate(trade_id, reason) explaining that no SSI exists internally or externally.

C. SSI exists but fields are wrong (malformed IBAN, wrong account, BIC ending "XXX"):
   → You do NOT know the correct values — only the counterparty does.
   → MUST call escalate(trade_id, reason) specifying: which field is wrong,
     what the current value is, and what information is needed from the counterparty.

D. Root cause is UNKNOWN (all checks passed but settlement still failed):
   → MUST call escalate(trade_id, reason) with a clear description of
     what further investigation is needed.

E. Value date error, instrument not found, or other data quality issues with no
   available tool fix:
   → Do NOT call any action tool. State the finding in recommended_action.

SWIFT rejection codes:
  AC01 — Account number incorrect/closed → SSI account is outdated (case C)
  AG01 — Transaction forbidden → counterparty inactive (case A)
  AM04 — Insufficient funds → liquidity issue, no tool action available
  BE01 — Inconsistent with end customer → BIC/IBAN mismatch (case C)

When multiple problems exist (e.g. inactive counterparty AND no SSI),
set root_cause=COMPOUND_FAILURE. Call tools for each fixable issue.

=== OUTPUT FORMAT ===

After all investigation and action tool calls are complete, output your final
message. It MUST be a raw JSON object — no markdown fences, no text before or
after the object:

{"diagnosis": "<findings>", "root_cause": "<MISSING_SSI|BIC_FORMAT_ERROR|IBAN_FORMAT_ERROR|INVALID_VALUE_DATE|INSTRUMENT_NOT_FOUND|COUNTERPARTY_NOT_FOUND|SWIFT_AC01|SWIFT_AG01|COMPOUND_FAILURE|UNKNOWN>", "recommended_action": "<next steps for the operator>"}
"""

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_agent(state: AgentState) -> str:
    """Decide what to do after the LLM responds."""
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return END
    for tc in last.tool_calls:
        if tc["name"] in _HITL_TOOL_TO_NODE:
            return _HITL_TOOL_TO_NODE[tc["name"]]
    return "read_tools"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_graph() -> Any:
    """Build and compile the STP triage LangGraph.

    Returns a compiled StateGraph with:
      - MemorySaver checkpointer (enables HITL via thread_id)
      - interrupt_before=["register_ssi_node"]
    """
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    ).bind_tools(ALL_TOOLS)

    read_tools_node = ToolNode(READ_ONLY_TOOLS)

    # ------------------------------------------------------------------
    # Node: agent
    # ------------------------------------------------------------------
    def agent_node(state: AgentState) -> dict[str, Any]:
        messages = list(state["messages"])
        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        _logger.info(
            "agent_node: invoking LLM",
            extra={"node": "agent", "trade_id": state.get("trade_id"), "message_count": len(messages)},
        )

        response = llm.invoke(messages)

        if response.tool_calls:
            for tc in response.tool_calls:
                _logger.info(
                    "agent_node: tool call planned",
                    extra={"node": "agent", "tool": tc["name"], "tool_args": tc["args"]},
                )
        else:
            _logger.info(
                "agent_node: final response (no tool calls)",
                extra={"node": "agent", "trade_id": state.get("trade_id")},
            )

        return {"messages": [response]}

    # ------------------------------------------------------------------
    # HITL node factory — each write tool gets its own node so that
    # interrupt_before can target it individually.
    # ------------------------------------------------------------------
    def _make_hitl_node(tool_name: str, tool_fn: Any) -> Any:
        def node(state: AgentState) -> dict[str, Any]:
            last = state["messages"][-1]
            tool_call = next(tc for tc in last.tool_calls if tc["name"] == tool_name)
            _logger.info(
                f"{tool_name}_node: executing (HITL approved)",
                extra={"node": f"{tool_name}_node", "trade_id": state.get("trade_id"),
                       "tool_args": tool_call["args"]},
            )
            result = tool_fn.invoke(tool_call["args"])
            return {
                "messages": [ToolMessage(content=result, tool_call_id=tool_call["id"])],
                "action_taken": True,
            }
        return node

    register_ssi_node = _make_hitl_node("register_ssi", register_ssi)
    reactivate_counterparty_node = _make_hitl_node("reactivate_counterparty", reactivate_counterparty)
    update_ssi_node = _make_hitl_node("update_ssi", update_ssi)
    escalate_node = _make_hitl_node("escalate", escalate)

    # ------------------------------------------------------------------
    # Assemble graph
    # ------------------------------------------------------------------
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("read_tools", read_tools_node)
    builder.add_node("register_ssi_node", register_ssi_node)
    builder.add_node("reactivate_counterparty_node", reactivate_counterparty_node)
    builder.add_node("update_ssi_node", update_ssi_node)
    builder.add_node("escalate_node", escalate_node)

    hitl_node_names = list(_HITL_TOOL_TO_NODE.values())

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
