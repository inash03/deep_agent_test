"""LangGraph ReAct BoAgent for Back-Office STP triage.

Graph topology:

  START
    │
    ▼
  [model_router_node]
    │
    ▼
  [agent_node] ◄─────────────────────────────────────┐
    │                                                 │
    │ _route_after_agent                              │
    ├─ register_ssi      ──► [register_ssi_node]      │ ← interrupt_before
    ├─ reactivate_cp     ──► [reactivate_cp_node]     │ ← interrupt_before
    ├─ update_ssi        ──► [update_ssi_node]        │ ← interrupt_before
    ├─ send_back_to_fo   ──► [send_back_to_fo_node]   │ ← interrupt_before
    ├─ other tool calls  ──► [read_tools_node]       ─┘
    └─ no tool calls     ──► END

HITL flow:
  - Graph pauses before any node in _BO_HITL_TOOL_TO_NODE
  - Caller checks get_state().next to identify which node is pending
  - On approval : graph.invoke(None, config)
  - On rejection: graph.update_state() injects rejection ToolMessage,
                  then graph.invoke(None, config) → back to agent_node
"""

from __future__ import annotations

import json
import logging
import operator
import os
from datetime import datetime, timezone
from typing import Annotated, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from src.infrastructure.tools import (
    BO_ALL_TOOLS,
    BO_READ_ONLY_TOOLS,
    reactivate_counterparty,
    register_ssi,
    send_back_to_fo,
    update_ssi,
)
from src.infrastructure.utils.cost_tracker import (
    MODEL_SONNET,
    call_with_cost_tracking,
    select_model,
)

# Maps each HITL tool name → the graph node that executes it
_BO_HITL_TOOL_TO_NODE: dict[str, str] = {
    "register_ssi": "register_ssi_node",
    "reactivate_counterparty": "reactivate_counterparty_node",
    "update_ssi": "update_ssi_node",
    "send_back_to_fo": "send_back_to_fo_node",
}

_logger = logging.getLogger("stp_triage.bo_agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

BO_SYSTEM_PROMPT = """\
You are a Back-Office (BO) STP exception triage agent at a securities firm.
Your job is to investigate BoCheck failures for a trade, resolve SSI / counterparty
issues where possible, and escalate or send back to FoAgent when appropriate.

=== INVESTIGATION STEPS (follow in order) ===

1. Call get_bo_check_results(trade_id) to retrieve BoCheck rule results.
   - Note: the response includes workflow_status and sendback_count.
   - If sendback_count >= 1, you may NOT use send_back_to_fo.
     Instead you MUST use escalate_to_bo_user.
   - If sendback_count >= 1, call get_fo_explanation(trade_id) to read
     the FoAgent's explanation before deciding on action.

2. Call get_trade_detail(trade_id) for full trade context
   (value_date, trade_date, instrument, amount).

3. For each FAILED BoCheck rule, investigate:
   - counterparty_exists / counterparty_active:
     → Call get_counterparty(lei) to verify.
   - ssi_exists:
     → Call get_settlement_instructions(lei, currency).
     → Call lookup_external_ssi(lei, currency) to check external source.
   - bic_format_valid / iban_format_valid:
     → Call get_settlement_instructions(lei, currency) to see current values.

4. Call get_counterparty_exception_history(lei) for pattern analysis.
   - If 3 or more failures in 30 days, include the warning in your diagnosis.

5. Call get_triage_history(trade_id) for past resolutions on the same trade.

=== CORRECTIVE ACTIONS (call tools — do not just recommend) ===

A. Inactive counterparty (counterparty_active failed):
   → MUST call reactivate_counterparty(lei). Operator will approve.

B. No internal SSI (ssi_exists failed):
   → MUST call lookup_external_ssi(lei, currency).
   → If data found: MUST call register_ssi(...) with those exact values.
   → If not found: MUST call escalate_to_bo_user(trade_id, reason)
     explaining that no SSI exists internally or externally.

C. SSI exists but BIC or IBAN is malformed (bic_format_valid / iban_format_valid failed):
   → You cannot know the correct values — only the counterparty does.
   → MUST call escalate_to_bo_user(trade_id, reason) specifying which field
     is wrong, the current value, and what information is needed.

D. Root cause is clearly FO-side (value date in past, instrument not found,
   amount error — issues unrelated to SSI / counterparty):
   → sendback_count == 0: MUST call send_back_to_fo(trade_id, reason).
     Operator will approve. Include specific details of what FO must fix.
   → sendback_count >= 1: MUST call escalate_to_bo_user(trade_id, reason)
     — a second sendback is prohibited.

E. UNKNOWN / all checks passed but settlement still failed:
   → MUST call escalate_to_bo_user(trade_id, reason) with a description
     of what further manual investigation is needed.

SWIFT rejection codes:
  AC01 — Account number incorrect/closed → SSI account outdated (case C)
  AG01 — Transaction forbidden → counterparty inactive (case A)
  AM04 — Insufficient funds → FO-side liquidity issue (case D)
  BE01 — Inconsistent with end customer → BIC/IBAN mismatch (case C)

Multiple problems: set root_cause=COMPOUND_FAILURE and call tools for each fixable issue.

=== OUTPUT FORMAT ===

After all investigation and action tool calls, output a raw JSON object (no markdown):

{"diagnosis": "<findings>", "root_cause": "<MISSING_SSI|BIC_FORMAT_ERROR|IBAN_FORMAT_ERROR|COUNTERPARTY_NOT_FOUND|SWIFT_AC01|SWIFT_AG01|COMPOUND_FAILURE|UNKNOWN>", "recommended_action": "<next steps>"}
"""

# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------


class BoAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    trade_id: str
    error_message: str
    action_taken: bool
    cost_log: Annotated[list[dict], operator.add]
    total_cost_usd: Annotated[float, operator.add]
    task_type: str
    selected_model: str


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def _route_after_agent(state: BoAgentState) -> str:
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return END
    # Once a HITL action has been approved and executed, prevent re-entering
    # any HITL node (LLM may try to call the same tool again after approval).
    if state.get("action_taken", False):
        return END
    for tc in last.tool_calls:
        if tc["name"] in _BO_HITL_TOOL_TO_NODE:
            return _BO_HITL_TOOL_TO_NODE[tc["name"]]
    return "read_tools"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_bo_graph() -> Any:
    """Build and compile the BoAgent LangGraph.

    Returns a compiled StateGraph with MemorySaver checkpointer and
    interrupt_before on all HITL nodes.
    """
    api_key = os.environ["ANTHROPIC_API_KEY"]
    _llm_by_model = {
        MODEL_SONNET: ChatAnthropic(model=MODEL_SONNET, api_key=api_key).bind_tools(BO_ALL_TOOLS),
        "claude-haiku-4-5-20251001": ChatAnthropic(
            model="claude-haiku-4-5-20251001", api_key=api_key
        ).bind_tools(BO_ALL_TOOLS),
    }

    read_tools_node = ToolNode(BO_READ_ONLY_TOOLS)

    def model_router_node(state: BoAgentState) -> dict[str, Any]:
        task_type = state.get("task_type") or "complex"
        total_cost = state.get("total_cost_usd") or 0.0
        model, reason = select_model(task_type, total_cost)
        log_entry = {
            "node": "model_router",
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _logger.info(
            "bo_model_router: model selected",
            extra={"model": model, "reason": reason, "trade_id": state.get("trade_id")},
        )
        return {"selected_model": model, "cost_log": [log_entry]}

    def agent_node(state: BoAgentState) -> dict[str, Any]:
        model = state.get("selected_model") or MODEL_SONNET
        llm = _llm_by_model.get(model, _llm_by_model[MODEL_SONNET])
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=BO_SYSTEM_PROMPT)] + messages
        _logger.info(
            "bo_agent_node: invoking LLM",
            extra={
                "node": "agent",
                "trade_id": state.get("trade_id"),
                "message_count": len(messages),
                "model": model,
            },
        )
        reason = f"selected_model={model}, task_type={state.get('task_type', 'complex')}"
        response, log_entry, cost = call_with_cost_tracking(llm, messages, "agent", model, reason)
        if response.tool_calls:
            for tc in response.tool_calls:
                _logger.info(
                    "bo_agent_node: tool call planned",
                    extra={"node": "agent", "tool": tc["name"], "tool_args": tc["args"]},
                )
        else:
            _logger.info(
                "bo_agent_node: final response",
                extra={"node": "agent", "trade_id": state.get("trade_id")},
            )
        return {"messages": [response], "cost_log": [log_entry], "total_cost_usd": cost}

    def _make_hitl_node(tool_name: str, tool_fn: Any) -> Any:
        def node(state: BoAgentState) -> dict[str, Any]:
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

    register_ssi_node = _make_hitl_node("register_ssi", register_ssi)
    reactivate_counterparty_node = _make_hitl_node("reactivate_counterparty", reactivate_counterparty)
    update_ssi_node = _make_hitl_node("update_ssi", update_ssi)
    send_back_to_fo_node = _make_hitl_node("send_back_to_fo", send_back_to_fo)

    builder = StateGraph(BoAgentState)

    builder.add_node("model_router", model_router_node)
    builder.add_node("agent", agent_node)
    builder.add_node("read_tools", read_tools_node)
    builder.add_node("register_ssi_node", register_ssi_node)
    builder.add_node("reactivate_counterparty_node", reactivate_counterparty_node)
    builder.add_node("update_ssi_node", update_ssi_node)
    builder.add_node("send_back_to_fo_node", send_back_to_fo_node)

    hitl_node_names = list(_BO_HITL_TOOL_TO_NODE.values())

    builder.add_edge(START, "model_router")
    builder.add_edge("model_router", "agent")
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
