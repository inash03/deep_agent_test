"""LangGraph BoAgent — Hybrid (Deterministic + Autonomous) architecture.

Graph topology:

  START
    │
    ▼
  [model_router_node]
    │
    ▼
  [gather_context_node]      ← deterministic: get_bo_check_results + get_trade_detail
    │                          sets triage_path, sendback_count, failed_rules in state
    │ _route_by_triage_path
    ├─ AG01        ──► [ag01_handler_node]
    │                       │ (synthetic AIMessage → reactivate_counterparty)
    │                       ▼
    │                  [reactivate_counterparty_node] ← interrupt_before (HITL)
    │                       │
    │                       ▼
    │                  [agent] ──► END  (action_taken=True → summary only)
    │
    ├─ MISSING_SSI ──► [lookup_ssi_node]
    │                       │ _route_after_ssi_lookup
    │                       ├─ found    ──► [prepare_register_ssi_node]
    │                       │                   │ (synthetic AIMessage → register_ssi)
    │                       │                   ▼
    │                       │              [register_ssi_node] ← interrupt_before (HITL)
    │                       │                   │
    │                       │                   ▼
    │                       │              [agent] ──► END
    │                       │
    │                       └─ not_found ──► [ssi_not_found_escalate_node]
    │                                            │ (calls escalate_to_bo_user directly)
    │                                            ▼
    │                                       [agent] ──► END
    │
    ├─ BE01        ──► [be01_handler_node]
    │                       │ (calls escalate_to_bo_user directly)
    │                       ▼
    │                  [agent] ──► END
    │
    ├─ AM04        ──► [fo_side_handler_node]
    │                       │ _route_after_fo_side_handler
    │                       ├─ sendback==0  ──► [send_back_to_fo_node] ← interrupt_before (HITL)
    │                       │                         │
    │                       │                         ▼
    │                       │                    [agent] ──► END
    │                       │
    │                       └─ sendback>=1  ──► [agent] ──► END  (action_taken=True)
    │
    └─ COMPOUND/UNKNOWN ──► [deep_investigation_node]  ← autonomous LLM reasoning
                                  │ _route_after_agent (unchanged)
                                  ├─ register_ssi      ──► [register_ssi_node_di]    ← interrupt_before
                                  ├─ reactivate_cp     ──► [reactivate_cp_node_di]   ← interrupt_before
                                  ├─ update_ssi        ──► [update_ssi_node_di]      ← interrupt_before
                                  ├─ send_back_to_fo   ──► [send_back_to_fo_node_di] ← interrupt_before
                                  ├─ other tool calls  ──► [read_tools_node] ─► loop
                                  └─ no tool calls     ──► END

HITL flow:
  - Graph pauses before any node in _BO_ALL_HITL_NODE_NAMES
  - Caller checks get_state().next to identify which node is pending
  - On approval : graph.invoke(None, config)
  - On rejection: graph.update_state() injects rejection ToolMessage (as_node=snapshot.next[0]),
                  then graph.invoke(None, config)
"""

from __future__ import annotations

import json
import logging
import operator
import os
from datetime import datetime, timezone
from typing import Annotated, Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from src.infrastructure.tools import (
    BO_ALL_TOOLS,
    BO_READ_ONLY_TOOLS,
    escalate_to_bo_user,
    get_bo_check_results,
    get_trade_detail,
    lookup_external_ssi,
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
from src.infrastructure.rag_service import _rag_service as _bo_rag_service

# Maps HITL tool name → deep_investigation path node (used by _route_after_agent)
_BO_HITL_TOOL_TO_NODE: dict[str, str] = {
    "register_ssi":            "register_ssi_node_di",
    "reactivate_counterparty": "reactivate_counterparty_node_di",
    "update_ssi":              "update_ssi_node_di",
    "send_back_to_fo":         "send_back_to_fo_node_di",
}

# All HITL node names across both deterministic and deep-investigation paths
_BO_ALL_HITL_NODE_NAMES: frozenset[str] = frozenset([
    "reactivate_counterparty_node",
    "register_ssi_node",
    "send_back_to_fo_node",
    "reactivate_counterparty_node_di",
    "register_ssi_node_di",
    "update_ssi_node_di",
    "send_back_to_fo_node_di",
])

# Triage path → handler node name
_TRIAGE_PATH_TO_NODE: dict[str, str] = {
    "AG01":        "ag01_handler",
    "MISSING_SSI": "lookup_ssi",
    "BE01":        "be01_handler",
    "AM04":        "fo_side_handler",
    "COMPOUND":    "deep_investigation",
    "UNKNOWN":     "deep_investigation",
}

_logger = logging.getLogger("stp_triage.bo_agent")

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

BO_SYSTEM_PROMPT = """\
You are a Back-Office (BO) STP exception triage agent at a securities firm.
Your job is to resolve SSI / counterparty issues and escalate or send back to FO when appropriate.
Context has already been gathered and is available in the conversation.

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

D. Root cause is clearly FO-side (value date in past, instrument not found, amount error):
   → sendback_count == 0: MUST call send_back_to_fo(trade_id, reason). Operator will approve.
   → sendback_count >= 1: MUST call escalate_to_bo_user(trade_id, reason).

E. UNKNOWN / all checks passed but settlement still failed:
   → MUST call escalate_to_bo_user(trade_id, reason).

CONSTRAINT: If sendback_count >= 1, you may NOT use send_back_to_fo. Use escalate_to_bo_user.
SWIFT codes: AC01=account closed/outdated, AG01=counterparty inactive, AM04=FO liquidity, BE01=BIC/IBAN mismatch.
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
    # Deterministic routing fields (populated by gather_context_node)
    triage_path: str        # "AG01"|"MISSING_SSI"|"BE01"|"AM04"|"UNKNOWN"|"COMPOUND"
    sendback_count: int
    failed_rules: list[str]
    counterparty_lei: str
    currency: str
    external_ssi_found: bool
    external_ssi_data: dict


# ---------------------------------------------------------------------------
# Pure routing functions
# ---------------------------------------------------------------------------


def _determine_triage_path(error_message: str, failed_rules: list[str]) -> str:
    em = error_message.upper()
    fs = set(failed_rules)
    conditions = {
        "AG01":        "AG01" in em or "counterparty_active" in fs,
        "BE01":        "BE01" in em or bool(fs & {"bic_format_valid", "iban_format_valid"}),
        "AM04":        "AM04" in em,
        "MISSING_SSI": "AC01" in em or "ssi_exists" in fs,
    }
    matched = [k for k, v in conditions.items() if v]
    if len(matched) > 1:
        return "COMPOUND"
    return matched[0] if matched else "UNKNOWN"


def _route_by_triage_path(state: BoAgentState) -> str:
    return _TRIAGE_PATH_TO_NODE.get(state.get("triage_path", "UNKNOWN"), "deep_investigation")


def _route_after_ssi_lookup(state: BoAgentState) -> str:
    return "prepare_register_ssi" if state.get("external_ssi_found") else "ssi_not_found_escalate"


def _route_after_fo_side_handler(state: BoAgentState) -> str:
    return "agent" if state.get("action_taken", False) else "send_back_to_fo_node"


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
    """Build and compile the BoAgent LangGraph (hybrid architecture).

    Returns a compiled StateGraph with PostgreSQL checkpointer and
    interrupt_before on all HITL nodes (deterministic + deep-investigation sets).
    """
    api_key = os.environ["ANTHROPIC_API_KEY"]
    _llm_by_model = {
        MODEL_SONNET: ChatAnthropic(model=MODEL_SONNET, api_key=api_key).bind_tools(BO_ALL_TOOLS),
        "claude-haiku-4-5-20251001": ChatAnthropic(
            model="claude-haiku-4-5-20251001", api_key=api_key
        ).bind_tools(BO_ALL_TOOLS),
    }

    read_tools_node = ToolNode(BO_READ_ONLY_TOOLS)

    # ------------------------------------------------------------------
    # Model router (unchanged)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Context gathering (deterministic, no LLM call)
    # ------------------------------------------------------------------

    def gather_context_node(state: BoAgentState) -> dict[str, Any]:
        trade_id = state["trade_id"]
        error_message = state.get("error_message", "")

        bo_raw = get_bo_check_results.invoke({"trade_id": trade_id})
        trade_raw = get_trade_detail.invoke({"trade_id": trade_id})
        bo_check = json.loads(bo_raw)
        trade = json.loads(trade_raw)

        # Fallback when DB is unavailable (test/mock environment)
        if "error" in bo_check:
            _logger.warning(
                "gather_context_node: DB unavailable, falling through to deep_investigation",
                extra={"trade_id": trade_id},
            )
            return {
                "triage_path": "UNKNOWN", "sendback_count": 0,
                "failed_rules": [], "counterparty_lei": "", "currency": "",
            }

        failed_rules = [
            r["rule_name"]
            for r in bo_check.get("results", [])
            if not r.get("passed", True)
        ]
        sendback_count = bo_check.get("sendback_count", 0)
        counterparty_lei = trade.get("counterparty_lei", "")
        currency = trade.get("settlement_currency") or trade.get("currency", "")
        triage_path = _determine_triage_path(error_message, failed_rules)

        context_msg = HumanMessage(content=(
            f"[Context pre-loaded] Trade: {trade_id} | LEI: {counterparty_lei} | "
            f"Currency: {currency} | Sendback: {sendback_count} | "
            f"Failed rules: {failed_rules} | Triage path: {triage_path}"
        ))
        _logger.info(
            "gather_context_node: triage_path=%s failed_rules=%s",
            triage_path, failed_rules,
            extra={"trade_id": trade_id, "triage_path": triage_path},
        )
        return {
            "messages": [context_msg],
            "triage_path": triage_path,
            "sendback_count": sendback_count,
            "failed_rules": failed_rules,
            "counterparty_lei": counterparty_lei,
            "currency": currency,
        }

    # ------------------------------------------------------------------
    # Deterministic handler nodes
    # ------------------------------------------------------------------

    def ag01_handler_node(state: BoAgentState) -> dict[str, Any]:
        trade_id = state["trade_id"]
        lei = state.get("counterparty_lei", "")
        tc_id = f"det_ag01_{trade_id}"
        _logger.info(
            "ag01_handler: injecting reactivate_counterparty",
            extra={"trade_id": trade_id, "lei": lei},
        )
        return {"messages": [AIMessage(
            content="AG01: counterparty inactive. Requesting reactivation.",
            tool_calls=[{"id": tc_id, "name": "reactivate_counterparty", "args": {"lei": lei}}],
        )]}

    def lookup_ssi_node(state: BoAgentState) -> dict[str, Any]:
        lei = state.get("counterparty_lei", "")
        currency = state.get("currency", "")
        raw = lookup_external_ssi.invoke({"lei": lei, "currency": currency})
        data = json.loads(raw)
        found = data.get("found", False)
        _logger.info(
            "lookup_ssi_node: external_ssi_found=%s",
            found,
            extra={"trade_id": state["trade_id"], "lei": lei, "currency": currency},
        )
        return {
            "external_ssi_found": found,
            "external_ssi_data": data if found else {},
        }

    def prepare_register_ssi_node(state: BoAgentState) -> dict[str, Any]:
        ssi = state.get("external_ssi_data", {})
        tc_id = f"det_register_ssi_{state['trade_id']}"
        _logger.info(
            "prepare_register_ssi_node: injecting register_ssi",
            extra={"trade_id": state["trade_id"]},
        )
        return {"messages": [AIMessage(
            content="External SSI found. Requesting registration.",
            tool_calls=[{"id": tc_id, "name": "register_ssi", "args": {
                "lei":      ssi.get("lei", state.get("counterparty_lei", "")),
                "currency": ssi.get("currency", state.get("currency", "")),
                "bic":      ssi.get("bic", ""),
                "account":  ssi.get("account", ""),
                "iban":     ssi.get("iban", ""),
            }}],
        )]}

    def ssi_not_found_escalate_node(state: BoAgentState) -> dict[str, Any]:
        trade_id = state["trade_id"]
        lei = state.get("counterparty_lei", "")
        currency = state.get("currency", "")
        reason = (
            f"No internal or external SSI found for LEI {lei!r} / currency {currency!r}. "
            "Manual counterparty SSI setup required."
        )
        raw = escalate_to_bo_user.invoke({"trade_id": trade_id, "reason": reason})
        _logger.info("ssi_not_found_escalate_node: escalated", extra={"trade_id": trade_id})
        return {
            "messages": [HumanMessage(content=f"[Escalated] {raw}")],
            "action_taken": True,
        }

    def be01_handler_node(state: BoAgentState) -> dict[str, Any]:
        trade_id = state["trade_id"]
        bad = [r for r in state.get("failed_rules", [])
               if r in ("bic_format_valid", "iban_format_valid")]
        reason = (
            f"BIC/IBAN format error (BE01) — failed rules: {bad}. "
            "Correct values must be sourced from the counterparty directly."
        )
        raw = escalate_to_bo_user.invoke({"trade_id": trade_id, "reason": reason})
        _logger.info("be01_handler_node: escalated", extra={"trade_id": trade_id})
        return {
            "messages": [HumanMessage(content=f"[Escalated] {raw}")],
            "action_taken": True,
        }

    def fo_side_handler_node(state: BoAgentState) -> dict[str, Any]:
        trade_id = state["trade_id"]
        sendback_count = state.get("sendback_count", 0)
        if sendback_count == 0:
            tc_id = f"det_sendback_{trade_id}"
            reason = f"AM04 liquidity issue — FO-side problem. {state.get('error_message', '')}"
            _logger.info(
                "fo_side_handler: injecting send_back_to_fo",
                extra={"trade_id": trade_id},
            )
            return {"messages": [AIMessage(
                content="AM04: FO-side issue. Sending back to FO.",
                tool_calls=[{"id": tc_id, "name": "send_back_to_fo",
                             "args": {"trade_id": trade_id, "reason": reason}}],
            )]}
        reason = (
            f"AM04 FO-side issue but sendback_count={sendback_count} — "
            "second sendback prohibited. Manual BO intervention required."
        )
        raw = escalate_to_bo_user.invoke({"trade_id": trade_id, "reason": reason})
        _logger.info(
            "fo_side_handler: escalated (sendback>=1)", extra={"trade_id": trade_id}
        )
        return {
            "messages": [HumanMessage(content=f"[Escalated] {raw}")],
            "action_taken": True,
        }

    # ------------------------------------------------------------------
    # RAG context node — enriches state before deep_investigation
    # ------------------------------------------------------------------

    def rag_context_node(state: BoAgentState) -> dict[str, Any]:
        """Retrieve similar past cases and inject them before deep investigation."""
        error_msg = state.get("error_message", "")
        failed_rules = state.get("failed_rules", [])
        query = f"{error_msg} failed_rules={failed_rules}"
        results = _bo_rag_service.search_similar(query, agent_type="bo", k=3)
        if not results:
            return {}
        rag_content = "[RAG Context — Similar past cases]\n" + "\n---\n".join(results)
        _logger.info(
            "rag_context_node: injected %d similar cases",
            len(results),
            extra={"trade_id": state.get("trade_id")},
        )
        return {"messages": [HumanMessage(content=rag_content)]}

    # ------------------------------------------------------------------
    # LLM nodes (shared implementation)
    # ------------------------------------------------------------------

    def _llm_invoke(state: BoAgentState, node_name: str) -> dict[str, Any]:
        model = state.get("selected_model") or MODEL_SONNET
        llm = _llm_by_model.get(model, _llm_by_model[MODEL_SONNET])
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=BO_SYSTEM_PROMPT)] + messages
        _logger.info(
            "%s: invoking LLM",
            node_name,
            extra={
                "node": node_name,
                "trade_id": state.get("trade_id"),
                "message_count": len(messages),
                "model": model,
            },
        )
        reason = f"selected_model={model}, task_type={state.get('task_type', 'complex')}"
        response, log_entry, cost = call_with_cost_tracking(llm, messages, node_name, model, reason)
        if response.tool_calls:
            for tc in response.tool_calls:
                _logger.info(
                    "%s: tool call planned",
                    node_name,
                    extra={"node": node_name, "tool": tc["name"], "tool_args": tc["args"]},
                )
        else:
            _logger.info(
                "%s: final response",
                node_name,
                extra={"node": node_name, "trade_id": state.get("trade_id")},
            )
        return {"messages": [response], "cost_log": [log_entry], "total_cost_usd": cost}

    def agent_node(state: BoAgentState) -> dict[str, Any]:
        # Summary pass: called after deterministic paths complete (action_taken=True)
        return _llm_invoke(state, "agent")

    def deep_investigation_node(state: BoAgentState) -> dict[str, Any]:
        # Autonomous investigation: called for UNKNOWN/COMPOUND cases
        return _llm_invoke(state, "deep_investigation")

    # ------------------------------------------------------------------
    # HITL node factory (unchanged)
    # ------------------------------------------------------------------

    def _make_hitl_node(tool_name: str, tool_fn: Any) -> Any:
        def node(state: BoAgentState) -> dict[str, Any]:
            last = state["messages"][-1]
            tool_call = next(tc for tc in last.tool_calls if tc["name"] == tool_name)
            _logger.info(
                "%s: executing (HITL approved)",
                tool_name,
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

    # Deterministic path HITL nodes (route back to "agent" for summary)
    reactivate_counterparty_node = _make_hitl_node("reactivate_counterparty", reactivate_counterparty)
    register_ssi_node = _make_hitl_node("register_ssi", register_ssi)
    send_back_to_fo_node = _make_hitl_node("send_back_to_fo", send_back_to_fo)

    # Deep investigation HITL nodes (route back to "deep_investigation" to continue loop)
    reactivate_counterparty_node_di = _make_hitl_node("reactivate_counterparty", reactivate_counterparty)
    register_ssi_node_di = _make_hitl_node("register_ssi", register_ssi)
    update_ssi_node_di = _make_hitl_node("update_ssi", update_ssi)
    send_back_to_fo_node_di = _make_hitl_node("send_back_to_fo", send_back_to_fo)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    builder = StateGraph(BoAgentState)

    # Core nodes
    builder.add_node("model_router",   model_router_node)
    builder.add_node("gather_context", gather_context_node)
    builder.add_node("agent",          agent_node)
    builder.add_node("rag_context",    rag_context_node)
    builder.add_node("deep_investigation", deep_investigation_node)
    builder.add_node("read_tools",     read_tools_node)

    # Deterministic handler nodes
    builder.add_node("ag01_handler",           ag01_handler_node)
    builder.add_node("lookup_ssi",             lookup_ssi_node)
    builder.add_node("prepare_register_ssi",   prepare_register_ssi_node)
    builder.add_node("ssi_not_found_escalate", ssi_not_found_escalate_node)
    builder.add_node("be01_handler",           be01_handler_node)
    builder.add_node("fo_side_handler",        fo_side_handler_node)

    # Deterministic HITL nodes (→ "agent" after execution)
    builder.add_node("reactivate_counterparty_node", reactivate_counterparty_node)
    builder.add_node("register_ssi_node",            register_ssi_node)
    builder.add_node("send_back_to_fo_node",         send_back_to_fo_node)

    # Deep investigation HITL nodes (→ "deep_investigation" after execution)
    builder.add_node("reactivate_counterparty_node_di", reactivate_counterparty_node_di)
    builder.add_node("register_ssi_node_di",            register_ssi_node_di)
    builder.add_node("update_ssi_node_di",              update_ssi_node_di)
    builder.add_node("send_back_to_fo_node_di",         send_back_to_fo_node_di)

    # START → model_router → gather_context → triage router
    builder.add_edge(START, "model_router")
    builder.add_edge("model_router", "gather_context")
    builder.add_conditional_edges(
        "gather_context",
        _route_by_triage_path,
        {
            "ag01_handler":       "ag01_handler",
            "lookup_ssi":         "lookup_ssi",
            "be01_handler":       "be01_handler",
            "fo_side_handler":    "fo_side_handler",
            # COMPOUND/UNKNOWN: pass through RAG context enrichment before deep investigation
            "deep_investigation": "rag_context",
        },
    )
    builder.add_edge("rag_context", "deep_investigation")

    # AG01 deterministic path
    builder.add_edge("ag01_handler", "reactivate_counterparty_node")
    builder.add_edge("reactivate_counterparty_node", "agent")

    # MISSING_SSI deterministic path
    builder.add_conditional_edges(
        "lookup_ssi",
        _route_after_ssi_lookup,
        {
            "prepare_register_ssi":   "prepare_register_ssi",
            "ssi_not_found_escalate": "ssi_not_found_escalate",
        },
    )
    builder.add_edge("prepare_register_ssi", "register_ssi_node")
    builder.add_edge("register_ssi_node",    "agent")
    builder.add_edge("ssi_not_found_escalate", "agent")

    # BE01 deterministic path
    builder.add_edge("be01_handler", "agent")

    # AM04 deterministic path
    builder.add_conditional_edges(
        "fo_side_handler",
        _route_after_fo_side_handler,
        {
            "send_back_to_fo_node": "send_back_to_fo_node",
            "agent":                "agent",
        },
    )
    builder.add_edge("send_back_to_fo_node", "agent")

    # Summary agent → END (action_taken=True guard in _route_after_agent ensures this)
    _di_routing = {
        **{n: n for n in _BO_HITL_TOOL_TO_NODE.values()},
        "read_tools": "read_tools",
        END: END,
    }
    builder.add_conditional_edges("agent", _route_after_agent, _di_routing)

    # Deep investigation loop
    builder.add_conditional_edges("deep_investigation", _route_after_agent, _di_routing)
    builder.add_edge("read_tools", "deep_investigation")
    for node_name in _BO_HITL_TOOL_TO_NODE.values():
        builder.add_edge(node_name, "deep_investigation")

    from src.infrastructure.db.checkpointer import get_checkpointer
    return builder.compile(
        checkpointer=get_checkpointer(),
        interrupt_before=list(_BO_ALL_HITL_NODE_NAMES),
    )
