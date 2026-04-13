"""Unit tests for domain entities and enums."""

import pytest
from pydantic import ValidationError

from src.domain.entities import (
    RootCause,
    STPFailure,
    Step,
    TriageResult,
    TriageStatus,
)


class TestRootCause:
    def test_all_values_exist(self):
        expected = {
            "MISSING_SSI",
            "BIC_FORMAT_ERROR",
            "INVALID_VALUE_DATE",
            "INSTRUMENT_NOT_FOUND",
            "COUNTERPARTY_NOT_FOUND",
            "UNKNOWN",
        }
        assert {e.value for e in RootCause} == expected

    def test_string_construction(self):
        assert RootCause("MISSING_SSI") == RootCause.MISSING_SSI

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            RootCause("NOT_A_REAL_CAUSE")


class TestTriageStatus:
    def test_values(self):
        assert TriageStatus.COMPLETED.value == "COMPLETED"
        assert TriageStatus.PENDING_APPROVAL.value == "PENDING_APPROVAL"


class TestSTPFailure:
    def test_valid(self):
        f = STPFailure(trade_id="TRD-001", error_message="SETT FAIL")
        assert f.trade_id == "TRD-001"

    def test_empty_trade_id_rejected(self):
        with pytest.raises(ValidationError):
            STPFailure(trade_id="", error_message="SETT FAIL")

    def test_empty_error_message_rejected(self):
        with pytest.raises(ValidationError):
            STPFailure(trade_id="TRD-001", error_message="")


class TestTriageResult:
    def test_completed_result(self):
        result = TriageResult(
            trade_id="TRD-001",
            status=TriageStatus.COMPLETED,
            diagnosis="SSI was missing.",
            root_cause=RootCause.MISSING_SSI,
            recommended_action="Register SSI.",
            action_taken=True,
        )
        assert result.status == TriageStatus.COMPLETED
        assert result.root_cause == RootCause.MISSING_SSI
        assert result.action_taken is True
        assert result.steps == []

    def test_pending_result(self):
        result = TriageResult(
            trade_id="TRD-001",
            status=TriageStatus.PENDING_APPROVAL,
            run_id="some-uuid",
            pending_action_description="Register SSI for LEI X / USD",
        )
        assert result.status == TriageStatus.PENDING_APPROVAL
        assert result.run_id == "some-uuid"
        assert result.diagnosis is None

    def test_step_appended(self):
        step = Step(
            step_type="tool_call",
            name="get_trade_detail",
            input={"trade_id": "TRD-001"},
            output={"trade_id": "TRD-001", "currency": "USD"},
        )
        result = TriageResult(
            trade_id="TRD-001",
            status=TriageStatus.COMPLETED,
            steps=[step],
        )
        assert len(result.steps) == 1
        assert result.steps[0].name == "get_trade_detail"
