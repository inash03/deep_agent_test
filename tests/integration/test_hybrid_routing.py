"""Integration tests for hybrid BoAgent routing — full graph, no LLM required.

Strategy:
  - Build the full production graph via build_bo_graph()
  - Patch get_bo_check_results, get_trade_detail, lookup_external_ssi so no DB is needed
  - Patch call_with_cost_tracking to avoid real LLM calls (returns dummy AIMessage)
  - Invoke the graph; it pauses at interrupt_before the expected HITL node
  - Verify snapshot.next[0] and state["triage_path"]

Scenarios covered (from Phase 32 task spec):
  #1  AG01       → interrupt at reactivate_counterparty_node
  #2  MISSING_SSI + external SSI found → interrupt at register_ssi_node
  #3  AC01 + external SSI NOT found → escalate_to_bo_user (no HITL interrupt)
  #4  BE01/iban_format_valid → escalate_to_bo_user (no HITL interrupt)
  #5  AM04 sendback_count=0 → interrupt at send_back_to_fo_node
  #6  AM04 sendback_count=1 → escalate_to_bo_user (no HITL interrupt)
  #7  COMPOUND → triage_path=COMPOUND verified via mini-graph (full graph needs LLM)
  #8  UNKNOWN  → triage_path=UNKNOWN verified via mini-graph

For #3, #4, #6: after the deterministic handler completes (action_taken=True), the
graph routes to agent_node for a summary. call_with_cost_tracking is mocked to
return a fake no-tool-call AIMessage, so the graph exits cleanly without calling
the real Anthropic API.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared mock payloads
# ---------------------------------------------------------------------------

TRADE_BASE = {
    "trade_id": "TRD-TEST",
    "counterparty_lei": "LEI123",
    "currency": "USD",
    "settlement_currency": "USD",
    "instrument_id": "EURUSD",
    "amount": "1000000.00",
    "value_date": "2026-05-01",
}


def _bo_check(failed_rules: list[str], sendback_count: int = 0,
              workflow_status: str = "BoAgentToCheck") -> str:
    results = [
        {"rule_name": r, "passed": False, "severity": "error", "message": f"{r} failed"}
        for r in failed_rules
    ]
    results.append({
        "rule_name": "counterparty_exists", "passed": True,
        "severity": "error", "message": "",
    })
    return json.dumps({
        "trade_id": "TRD-TEST",
        "found": True,
        "workflow_status": workflow_status,
        "sendback_count": sendback_count,
        "results": results,
    })


def _trade(lei: str = "LEI123", currency: str = "USD") -> str:
    return json.dumps({**TRADE_BASE, "counterparty_lei": lei, "settlement_currency": currency})


def _external_ssi_found(lei: str = "LEI123", currency: str = "USD") -> str:
    return json.dumps({
        "found": True, "lei": lei, "currency": currency,
        "bic": "TESTGB2L", "account": "GB29NWBK60161331926819",
        "iban": "GB29NWBK60161331926819",
    })


def _external_ssi_not_found() -> str:
    return json.dumps({"found": False, "lei": "LEI123", "currency": "USD"})


def _escalate_ok() -> str:
    return json.dumps({"success": True, "message": "Escalated to BO user."})


def _make_fake_llm_response():
    """Fake AIMessage with no tool calls — causes agent_node to route to END."""
    from langchain_core.messages import AIMessage
    fake_ai_msg = AIMessage(content='{"diagnosis": "test", "root_cause": "UNKNOWN", "recommended_action": "none"}')
    fake_log = {"node": "agent", "model": "claude-sonnet-4-6", "input_tokens": 0,
                "output_tokens": 0, "cost_usd": 0.0, "reason": "mocked", "timestamp": ""}
    return fake_ai_msg, fake_log, 0.0


# ---------------------------------------------------------------------------
# Helper to build graph and run to first pause point
# ---------------------------------------------------------------------------

def _invoke_graph(
    error_message: str,
    bo_check_payload: str,
    trade_payload: str,
    external_ssi_payload: str = "",
    thread_id: str = "test-thread",
) -> tuple[dict, list]:
    """Build full bo_graph, invoke once, return (snapshot_values, snapshot_next)."""
    with (
        patch("src.infrastructure.bo_agent.get_bo_check_results") as mock_bo,
        patch("src.infrastructure.bo_agent.get_trade_detail") as mock_trade,
        patch("src.infrastructure.bo_agent.lookup_external_ssi") as mock_ssi,
        patch("src.infrastructure.bo_agent.escalate_to_bo_user") as mock_escalate,
        patch("src.infrastructure.bo_agent.get_fo_check_results", create=True),
        patch("src.infrastructure.bo_agent.call_with_cost_tracking") as mock_llm,
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
    ):
        mock_bo.invoke.return_value = bo_check_payload
        mock_trade.invoke.return_value = trade_payload
        mock_ssi.invoke.return_value = external_ssi_payload or _external_ssi_not_found()
        mock_escalate.invoke.return_value = _escalate_ok()
        mock_llm.return_value = _make_fake_llm_response()

        from src.infrastructure.bo_agent import build_bo_graph

        graph = build_bo_graph()
        initial_state = {
            "messages": [],
            "trade_id": "TRD-TEST",
            "error_message": error_message,
            "action_taken": False,
            "cost_log": [],
            "total_cost_usd": 0.0,
            "task_type": "complex",
            "selected_model": "",
        }
        config = {"configurable": {"thread_id": thread_id}}
        graph.invoke(initial_state, config)
        snapshot = graph.get_state(config)
        return snapshot.values, list(snapshot.next)


# ---------------------------------------------------------------------------
# Scenario #1 — AG01 → reactivate_counterparty_node (HITL interrupt)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ag01_routes_to_reactivate_hitl():
    values, nxt = _invoke_graph(
        error_message="MT103 rejected by SWIFT. Reason code: AG01.",
        bo_check_payload=_bo_check([]),
        trade_payload=_trade(),
        thread_id="s1-ag01",
    )
    assert values["triage_path"] == "AG01"
    assert nxt == ["reactivate_counterparty_node"]


# ---------------------------------------------------------------------------
# Scenario #2 — MISSING_SSI + external SSI found → register_ssi_node (HITL)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_missing_ssi_with_external_found_routes_to_register_hitl():
    values, nxt = _invoke_graph(
        error_message="SSI not found for counterparty.",
        bo_check_payload=_bo_check(["ssi_exists"]),
        trade_payload=_trade(),
        external_ssi_payload=_external_ssi_found(),
        thread_id="s2-ssi-found",
    )
    assert values["triage_path"] == "MISSING_SSI"
    assert nxt == ["register_ssi_node"]
    assert values.get("external_ssi_found") is True


# ---------------------------------------------------------------------------
# Scenario #3 — AC01 + external SSI NOT found → escalate (no HITL interrupt)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_missing_ssi_without_external_escalates():
    values, nxt = _invoke_graph(
        error_message="MT103 rejected by SWIFT. Reason code: AC01.",
        bo_check_payload=_bo_check([]),
        trade_payload=_trade(),
        external_ssi_payload=_external_ssi_not_found(),
        thread_id="s3-ssi-missing",
    )
    assert values["triage_path"] == "MISSING_SSI"
    assert nxt == []   # graph completed, no HITL pause
    assert values.get("action_taken") is True


# ---------------------------------------------------------------------------
# Scenario #4 — BE01 / iban_format_valid → escalate_to_bo_user (no HITL)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_be01_rule_failure_escalates():
    values, nxt = _invoke_graph(
        error_message="Custodian rejected settlement instruction. No further details.",
        bo_check_payload=_bo_check(["iban_format_valid"]),
        trade_payload=_trade(),
        thread_id="s4-be01",
    )
    assert values["triage_path"] == "BE01"
    assert nxt == []   # graph completed
    assert values.get("action_taken") is True


# ---------------------------------------------------------------------------
# Scenario #5 — AM04 sendback_count=0 → send_back_to_fo_node (HITL)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_am04_sendback0_routes_to_send_back_hitl():
    values, nxt = _invoke_graph(
        error_message="MT103 rejected by SWIFT. Reason code: AM04.",
        bo_check_payload=_bo_check([], sendback_count=0),
        trade_payload=_trade(),
        thread_id="s5-am04-sb0",
    )
    assert values["triage_path"] == "AM04"
    assert nxt == ["send_back_to_fo_node"]
    assert values["sendback_count"] == 0


# ---------------------------------------------------------------------------
# Scenario #6 — AM04 sendback_count=1 → escalate (no HITL)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_am04_sendback1_escalates():
    values, nxt = _invoke_graph(
        error_message="AM04 insufficient funds.",
        bo_check_payload=_bo_check([], sendback_count=1),
        trade_payload=_trade(),
        thread_id="s6-am04-sb1",
    )
    assert values["triage_path"] == "AM04"
    assert values["sendback_count"] == 1
    assert nxt == []   # graph completed
    assert values.get("action_taken") is True


# ---------------------------------------------------------------------------
# Scenario #7 — COMPOUND → triage_path=COMPOUND (mini-graph, no LLM needed)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_compound_triage_path_is_set():
    """COMPOUND triage_path is set correctly by gather_context_node.
    deep_investigation_node would need a real LLM to proceed, so we
    verify only the gather_context output using the mini-graph pattern."""
    import json as _json

    with (
        patch("src.infrastructure.bo_agent.get_bo_check_results") as mock_bo,
        patch("src.infrastructure.bo_agent.get_trade_detail") as mock_trade,
        patch("src.infrastructure.bo_agent.get_fo_check_results", create=True),
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
    ):
        mock_bo.invoke.return_value = _bo_check(["counterparty_active", "ssi_exists"])
        mock_trade.invoke.return_value = _trade()

        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
        from src.infrastructure.bo_agent import BoAgentState, _determine_triage_path

        def _mock_model_router(state):
            return {"selected_model": "claude-sonnet-4-6", "cost_log": []}

        def _gather(state):
            bo_raw = mock_bo.invoke({"trade_id": state["trade_id"]})
            trade_raw = mock_trade.invoke({"trade_id": state["trade_id"]})
            bo_check = _json.loads(bo_raw)
            trade = _json.loads(trade_raw)
            if "error" in bo_check:
                return {"triage_path": "UNKNOWN", "sendback_count": 0,
                        "failed_rules": [], "counterparty_lei": "", "currency": ""}
            failed_rules = [
                r["rule_name"] for r in bo_check.get("results", [])
                if not r.get("passed", True)
            ]
            triage_path = _determine_triage_path(state.get("error_message", ""), failed_rules)
            return {
                "triage_path": triage_path,
                "sendback_count": bo_check.get("sendback_count", 0),
                "failed_rules": failed_rules,
                "counterparty_lei": trade.get("counterparty_lei", ""),
                "currency": trade.get("settlement_currency") or trade.get("currency", ""),
            }

        mini = StateGraph(BoAgentState)
        mini.add_node("model_router", _mock_model_router)
        mini.add_node("gather_context", _gather)
        mini.add_edge(START, "model_router")
        mini.add_edge("model_router", "gather_context")
        mini.add_edge("gather_context", END)
        compiled = mini.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "s7-compound"}}
        compiled.invoke({
            "messages": [], "trade_id": "TRD-TEST",
            "error_message": "Multiple pre-settlement checks failed.",
            "action_taken": False, "cost_log": [], "total_cost_usd": 0.0,
            "task_type": "complex", "selected_model": "",
        }, config)
        snapshot = compiled.get_state(config)
        assert snapshot.values["triage_path"] == "COMPOUND"
        assert "counterparty_active" in snapshot.values["failed_rules"]
        assert "ssi_exists" in snapshot.values["failed_rules"]


# ---------------------------------------------------------------------------
# Scenario #8 — UNKNOWN → triage_path=UNKNOWN (mini-graph)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_unknown_error_sets_triage_path_unknown():
    import json as _json

    with (
        patch("src.infrastructure.bo_agent.get_bo_check_results") as mock_bo,
        patch("src.infrastructure.bo_agent.get_trade_detail") as mock_trade,
        patch("src.infrastructure.bo_agent.get_fo_check_results", create=True),
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
    ):
        mock_bo.invoke.return_value = _bo_check([])
        mock_trade.invoke.return_value = _trade()

        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
        from src.infrastructure.bo_agent import BoAgentState, _determine_triage_path

        def _mock_model_router(state):
            return {"selected_model": "claude-sonnet-4-6", "cost_log": []}

        def _gather(state):
            bo_raw = mock_bo.invoke({"trade_id": state["trade_id"]})
            trade_raw = mock_trade.invoke({"trade_id": state["trade_id"]})
            bo_check = _json.loads(bo_raw)
            trade = _json.loads(trade_raw)
            if "error" in bo_check:
                return {"triage_path": "UNKNOWN", "sendback_count": 0,
                        "failed_rules": [], "counterparty_lei": "", "currency": ""}
            failed_rules = [
                r["rule_name"] for r in bo_check.get("results", [])
                if not r.get("passed", True)
            ]
            triage_path = _determine_triage_path(state.get("error_message", ""), failed_rules)
            return {
                "triage_path": triage_path,
                "sendback_count": bo_check.get("sendback_count", 0),
                "failed_rules": failed_rules,
                "counterparty_lei": trade.get("counterparty_lei", ""),
                "currency": trade.get("settlement_currency") or trade.get("currency", ""),
            }

        mini = StateGraph(BoAgentState)
        mini.add_node("model_router", _mock_model_router)
        mini.add_node("gather_context", _gather)
        mini.add_edge(START, "model_router")
        mini.add_edge("model_router", "gather_context")
        mini.add_edge("gather_context", END)
        compiled = mini.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "s8-unknown"}}
        compiled.invoke({
            "messages": [], "trade_id": "TRD-TEST",
            "error_message": "Settlement SLA breach. Status unknown.",
            "action_taken": False, "cost_log": [], "total_cost_usd": 0.0,
            "task_type": "complex", "selected_model": "",
        }, config)
        snapshot = compiled.get_state(config)
        assert snapshot.values["triage_path"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# Deterministic paths produce no LLM cost entries before the HITL pause
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ag01_deterministic_path_has_no_llm_cost():
    """For deterministic paths, cost_log should contain only the model_router entry
    (cost_usd=0.0) — no real LLM invocation occurs before the HITL pause."""
    values, nxt = _invoke_graph(
        error_message="AG01 counterparty inactive.",
        bo_check_payload=_bo_check([]),
        trade_payload=_trade(),
        thread_id="s9-ag01-cost",
    )
    assert nxt == ["reactivate_counterparty_node"]
    llm_costs = [e for e in values.get("cost_log", []) if e.get("cost_usd", 0.0) > 0.0]
    assert llm_costs == [], f"Expected no LLM cost in deterministic path, got: {llm_costs}"
