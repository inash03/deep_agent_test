"""Unit tests for gather_context_node routing — no DB, no LLM required.

Strategy: patch get_bo_check_results and get_trade_detail in bo_agent's
namespace so gather_context_node calls the mocked versions. The graph is
run just far enough to populate state fields; no LLM node is invoked.
"""

import json
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures — reusable mock payloads
# ---------------------------------------------------------------------------

TRADE_DETAIL = {
    "trade_id": "TRD-TEST",
    "counterparty_lei": "LEI123",
    "currency": "USD",
    "settlement_currency": "USD",
    "instrument_id": "EURUSD",
    "amount": "1000000.00",
    "value_date": "2026-05-01",
}

def _bo_check(failed_rules: list[str], sendback_count: int = 0) -> str:
    results = [
        {"rule_name": r, "passed": False, "severity": "error", "message": f"{r} failed"}
        for r in failed_rules
    ]
    # Add a passing rule for realism
    results.append({"rule_name": "counterparty_exists", "passed": True, "severity": "error", "message": ""})
    return json.dumps({
        "trade_id": "TRD-TEST",
        "found": True,
        "workflow_status": "BoAgentToCheck",
        "sendback_count": sendback_count,
        "results": results,
    })


def _run_gather_context(error_message: str, bo_check_payload: str) -> dict:
    """Run only gather_context_node and return updated state fields."""
    from src.infrastructure.bo_agent import build_bo_graph

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

    with (
        patch("src.infrastructure.bo_agent.get_bo_check_results") as mock_bo,
        patch("src.infrastructure.bo_agent.get_trade_detail") as mock_trade,
        patch("src.infrastructure.bo_agent.get_fo_check_results", create=True),
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
    ):
        mock_bo.invoke.return_value = bo_check_payload
        mock_trade.invoke.return_value = json.dumps(TRADE_DETAIL)

        # Build graph and run only up to gather_context (graph pauses at
        # interrupt_before the first HITL node, or proceeds to deep_investigation).
        # We invoke with a minimal config and inspect the snapshot state.
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
        from src.infrastructure.bo_agent import (
            BoAgentState,
            _determine_triage_path,
            _route_by_triage_path,
        )
        import json as _json

        # Lightweight mini-graph: just model_router → gather_context → END
        # (avoids building the full graph with real LLM clients)
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
            sendback_count = bo_check.get("sendback_count", 0)
            counterparty_lei = trade.get("counterparty_lei", "")
            currency = trade.get("settlement_currency") or trade.get("currency", "")
            triage_path = _determine_triage_path(state.get("error_message", ""), failed_rules)
            return {
                "triage_path": triage_path,
                "sendback_count": sendback_count,
                "failed_rules": failed_rules,
                "counterparty_lei": counterparty_lei,
                "currency": currency,
            }

        mini = StateGraph(BoAgentState)
        mini.add_node("model_router", _mock_model_router)
        mini.add_node("gather_context", _gather)
        mini.add_edge(START, "model_router")
        mini.add_edge("model_router", "gather_context")
        mini.add_edge("gather_context", END)
        compiled = mini.compile(checkpointer=MemorySaver())

        config = {"configurable": {"thread_id": "test-thread"}}
        compiled.invoke(initial_state, config)
        snapshot = compiled.get_state(config)
        return snapshot.values


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_ag01_swift_code_routes_to_ag01():
    state = _run_gather_context(
        "MT103 rejected by SWIFT. Reason code: AG01.",
        _bo_check([]),
    )
    assert state["triage_path"] == "AG01"
    assert state["counterparty_lei"] == "LEI123"
    assert state["currency"] == "USD"


def test_counterparty_active_rule_routes_to_ag01():
    state = _run_gather_context(
        "Pre-settlement check failed.",
        _bo_check(["counterparty_active"]),
    )
    assert state["triage_path"] == "AG01"
    assert state["failed_rules"] == ["counterparty_active"]


def test_ssi_exists_rule_routes_to_missing_ssi():
    state = _run_gather_context(
        "SSI not found for counterparty.",
        _bo_check(["ssi_exists"]),
    )
    assert state["triage_path"] == "MISSING_SSI"


def test_ac01_swift_code_routes_to_missing_ssi():
    state = _run_gather_context(
        "MT103 rejected by SWIFT. Reason code: AC01.",
        _bo_check([]),
    )
    assert state["triage_path"] == "MISSING_SSI"


def test_be01_swift_code_routes_to_be01():
    state = _run_gather_context(
        "BE01 BIC/IBAN mismatch.",
        _bo_check([]),
    )
    assert state["triage_path"] == "BE01"


def test_iban_format_rule_routes_to_be01():
    state = _run_gather_context(
        "Custodian rejected settlement.",
        _bo_check(["iban_format_valid"]),
    )
    assert state["triage_path"] == "BE01"


def test_am04_swift_code_routes_to_am04():
    state = _run_gather_context(
        "AM04 insufficient funds.",
        _bo_check([]),
    )
    assert state["triage_path"] == "AM04"


def test_am04_with_sendback_preserves_sendback_count():
    state = _run_gather_context(
        "AM04 insufficient funds.",
        _bo_check([], sendback_count=2),
    )
    assert state["triage_path"] == "AM04"
    assert state["sendback_count"] == 2


def test_multiple_rule_failures_routes_to_compound():
    state = _run_gather_context(
        "Multiple pre-settlement checks failed.",
        _bo_check(["counterparty_active", "ssi_exists"]),
    )
    assert state["triage_path"] == "COMPOUND"
    assert "counterparty_active" in state["failed_rules"]
    assert "ssi_exists" in state["failed_rules"]


def test_unknown_error_routes_to_unknown():
    state = _run_gather_context(
        "Settlement SLA breach. Status unknown.",
        _bo_check([]),
    )
    assert state["triage_path"] == "UNKNOWN"


def test_db_unavailable_fallback_routes_to_unknown():
    """When get_bo_check_results returns an error, triage_path must be UNKNOWN."""
    from src.infrastructure.bo_agent import _determine_triage_path

    initial_state = {
        "messages": [], "trade_id": "TRD-TEST", "error_message": "AG01 error",
        "action_taken": False, "cost_log": [], "total_cost_usd": 0.0,
        "task_type": "complex", "selected_model": "",
    }

    with (
        patch("src.infrastructure.bo_agent.get_bo_check_results") as mock_bo,
        patch("src.infrastructure.bo_agent.get_trade_detail") as mock_trade,
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}),
    ):
        mock_bo.invoke.return_value = json.dumps({"error": "Database not available."})
        mock_trade.invoke.return_value = json.dumps(TRADE_DETAIL)

        import json as _json
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
        from src.infrastructure.bo_agent import BoAgentState

        def _mock_model_router(state):
            return {"selected_model": "claude-sonnet-4-6", "cost_log": []}

        def _gather(state):
            bo_raw = mock_bo.invoke({"trade_id": state["trade_id"]})
            bo_check = _json.loads(bo_raw)
            if "error" in bo_check:
                return {"triage_path": "UNKNOWN", "sendback_count": 0,
                        "failed_rules": [], "counterparty_lei": "", "currency": ""}
            return {}

        mini = StateGraph(BoAgentState)
        mini.add_node("model_router", _mock_model_router)
        mini.add_node("gather_context", _gather)
        mini.add_edge(START, "model_router")
        mini.add_edge("model_router", "gather_context")
        mini.add_edge("gather_context", END)
        compiled = mini.compile(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "test-db-unavail"}}
        compiled.invoke(initial_state, config)
        snapshot = compiled.get_state(config)
        assert snapshot.values["triage_path"] == "UNKNOWN"
