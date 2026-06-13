"""Step definitions for the BO triage HITL resume features.

Covers:
  - features/bo_triage_hitl.feature          (business behavior)
  - features/specs/bo_triage_hitl.spec.feature (detailed AG01 boundary)

These are CHARACTERIZATION tests for already-built behavior (FR-06 retrofit):
they document and lock the existing resume (approve/reject) path, which had no
test before. The full production BoAgent graph is built, but every external
boundary is mocked (BO check, trade detail, the reactivate tool, the LLM, and
the RAG store), so the scenarios are deterministic with no real DB, LLM, or
network — consistent with docs/testing.md. The in-process MemorySaver
checkpointer is used because DATABASE_URL is unset in the test harness.
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage
from pytest_bdd import given, parsers, scenarios, then, when

from src.domain.entities import TriageStatus

scenarios("../../features/bo_triage_hitl.feature")
scenarios("../../features/specs/bo_triage_hitl.spec.feature")

_AG01_ERROR = "MT103 rejected by SWIFT. Reason code: AG01."


def _bo_check() -> str:
    return json.dumps(
        {
            "trade_id": "TRD-TEST",
            "found": True,
            "workflow_status": "BoAgentToCheck",
            "sendback_count": 0,
            "results": [
                {"rule_name": "counterparty_exists", "passed": True,
                 "severity": "error", "message": ""},
            ],
        }
    )


def _trade() -> str:
    return json.dumps(
        {
            "trade_id": "TRD-TEST",
            "counterparty_lei": "LEI123",
            "currency": "USD",
            "settlement_currency": "USD",
            "instrument_id": "EURUSD",
            "amount": "1000000.00",
            "value_date": "2026-05-01",
        }
    )


def _fake_llm_response():
    msg = AIMessage(
        content='{"diagnosis": "Counterparty was inactive.", '
        '"root_cause": "SWIFT_AG01", "recommended_action": "Reactivated."}'
    )
    log = {"node": "agent", "model": "claude-sonnet-4-6", "input_tokens": 0,
           "output_tokens": 0, "cost_usd": 0.0, "reason": "mocked", "timestamp": ""}
    return msg, log, 0.0


@pytest.fixture
def bo_hitl():
    """Fully-mocked BoTriageUseCase for the AG01 HITL path. No DB/LLM/network."""
    with ExitStack() as stack:
        def p(target: str) -> MagicMock:
            return stack.enter_context(patch(target))

        mock_bo = p("src.infrastructure.bo_agent.get_bo_check_results")
        mock_trade = p("src.infrastructure.bo_agent.get_trade_detail")
        mock_reactivate = p("src.infrastructure.bo_agent.reactivate_counterparty")
        mock_llm = p("src.infrastructure.bo_agent.call_with_cost_tracking")
        stack.enter_context(patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}))
        # Neutralize the optional RAG store (no embeddings / DB in tests).
        stack.enter_context(
            patch("src.infrastructure.bo_triage_use_case._bo_rag_svc", MagicMock())
        )

        mock_bo.invoke.return_value = _bo_check()
        mock_trade.invoke.return_value = _trade()
        mock_reactivate.invoke.return_value = json.dumps(
            {"success": True, "message": "Counterparty reactivated."}
        )
        mock_llm.return_value = _fake_llm_response()

        from src.infrastructure.bo_triage_use_case import BoTriageUseCase

        yield SimpleNamespace(uc=BoTriageUseCase(), reactivate=mock_reactivate)


@given("a BO triage run paused awaiting approval to reactivate a counterparty",
       target_fixture="run")
@given("a BO triage run paused at the reactivate-counterparty approval",
       target_fixture="run")
def _start_paused(bo_hitl) -> dict:
    started = bo_hitl.uc.start(trade_id="TRD-TEST", error_context=_AG01_ERROR)
    assert started.status == TriageStatus.PENDING_APPROVAL
    return {"started": started, "result": started}


@when("the operator approves the pending action")
def _approve(bo_hitl, run) -> None:
    run["result"] = bo_hitl.uc.resume(run["started"].run_id, approved=True)


@when("the operator rejects the pending action")
def _reject(bo_hitl, run) -> None:
    run["result"] = bo_hitl.uc.resume(run["started"].run_id, approved=False)


@when(parsers.parse('the operator resumes with approved "{approved}"'))
def _resume(bo_hitl, run, approved: str) -> None:
    run["result"] = bo_hitl.uc.resume(run["started"].run_id, approved=(approved == "true"))


@then("the triage run completes")
def _completes(run) -> None:
    assert run["result"].status == TriageStatus.COMPLETED


@then(parsers.parse('the triage status is "{status}"'))
def _status(run, status: str) -> None:
    assert run["result"].status.value == status


@then(parsers.parse('the pending action type is "{action_type}"'))
def _pending_type(run, action_type: str) -> None:
    assert run["result"].pending_action_type == action_type


@then("the reactivation is executed")
def _executed(bo_hitl) -> None:
    bo_hitl.reactivate.invoke.assert_called_once()


@then("the reactivation is not executed")
def _not_executed(bo_hitl) -> None:
    bo_hitl.reactivate.invoke.assert_not_called()


@then("the action is recorded as taken")
def _taken(run) -> None:
    assert run["result"].action_taken is True


@then("the action is recorded as not taken")
def _not_taken(run) -> None:
    assert run["result"].action_taken is False


@then(parsers.parse('action_taken is "{flag}"'))
def _action_flag(run, flag: str) -> None:
    assert run["result"].action_taken is (flag == "true")


@then(parsers.parse("the reactivate tool was called {calls:d} times"))
def _call_count(bo_hitl, calls: int) -> None:
    assert bo_hitl.reactivate.invoke.call_count == calls
