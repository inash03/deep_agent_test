"""Requirement-driven tests for API boundary contracts.

These tests assert business/API requirements without using a real database,
network, LLM provider, or MCP service.
"""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.presentation.dependencies import verify_api_key
from src.presentation.routers.trade_events import create_trade_event
from src.presentation.schemas import TradeCreateRequest, TradeEventCreateRequest


def test_trade_create_request_rejects_non_positive_amount() -> None:
    """FR-01 creates trades, but operations must not accept zero-value trades."""
    with pytest.raises(ValidationError):
        TradeCreateRequest(
            trade_date=date(2026, 5, 1),
            value_date=date(2026, 5, 5),
            counterparty_lei="254900CUSTBANK000001",
            instrument_id="EURUSD",
            currency="USD",
            amount=Decimal("0"),
            fx_rate=Decimal("1.10000000"),
        )


def test_trade_create_request_rejects_non_positive_fx_rate() -> None:
    """FX trade creation requires a positive conversion rate at the API boundary."""
    with pytest.raises(ValidationError):
        TradeCreateRequest(
            trade_date=date(2026, 5, 1),
            value_date=date(2026, 5, 5),
            counterparty_lei="254900CUSTBANK000001",
            instrument_id="EURUSD",
            currency="USD",
            amount=Decimal("1000000"),
            fx_rate=Decimal("0"),
        )


def test_trade_create_request_ignores_client_supplied_trade_id() -> None:
    """FR-01 requires the server to allocate trade IDs instead of trusting clients."""
    body = TradeCreateRequest(
        trade_id="TRD-CLIENT-SUPPLIED",
        trade_date=date(2026, 5, 1),
        value_date=date(2026, 5, 5),
        counterparty_lei="254900CUSTBANK000001",
        instrument_id="EURUSD",
        currency="USD",
        amount=Decimal("1000000"),
        fx_rate=Decimal("1.10000000"),
    )

    assert not hasattr(body, "trade_id")


def test_api_key_is_not_required_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Local development can run without manual secret setup when API_KEY is unset."""
    monkeypatch.delenv("API_KEY", raising=False)

    assert asyncio.run(verify_api_key(api_key=None)) is None  # type: ignore[arg-type]


def test_api_key_rejects_missing_or_wrong_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security requirement: protected FastAPI endpoints validate X-API-Key."""
    monkeypatch.setenv("API_KEY", "expected-key")

    with pytest.raises(HTTPException) as missing:
        asyncio.run(verify_api_key(api_key=None))  # type: ignore[arg-type]
    with pytest.raises(HTTPException) as wrong:
        asyncio.run(verify_api_key(api_key="wrong-key"))

    assert missing.value.status_code == 401
    assert wrong.value.status_code == 401


def test_api_key_accepts_configured_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """A correct BFF-provided API key should pass the FastAPI security gate."""
    monkeypatch.setenv("API_KEY", "expected-key")

    assert asyncio.run(verify_api_key(api_key="expected-key")) is None


def test_amend_event_requires_amended_fields_before_db_access() -> None:
    """FR-08: an AMEND request must specify what trade fields are being amended."""
    body = TradeEventCreateRequest(
        event_type="AMEND",
        reason="Correct settlement date",
        requested_by="fo_user_01",
    )

    with pytest.raises(HTTPException) as exc:
        create_trade_event("TRD-001", body, db=None)  # type: ignore[arg-type]

    assert exc.value.status_code == 422
    assert "amended_fields is required" in str(exc.value.detail)


def test_trade_event_rejects_unknown_event_type_before_db_access() -> None:
    """FR-08 supports only explicit AMEND and CANCEL event lifecycles."""
    body = TradeEventCreateRequest(
        event_type="REBOOK",
        reason="Unsupported event",
        requested_by="fo_user_01",
    )

    with pytest.raises(HTTPException) as exc:
        create_trade_event("TRD-001", body, db=None)  # type: ignore[arg-type]

    assert exc.value.status_code == 422
    assert "event_type must be AMEND or CANCEL" in str(exc.value.detail)


# ---------------------------------------------------------------------------
# Positive / happy-path schema tests
# ---------------------------------------------------------------------------


def test_trade_create_request_accepts_valid_input() -> None:
    """FR-01 happy path: a well-formed trade request is accepted without error."""
    body = TradeCreateRequest(
        trade_date=date(2026, 5, 1),
        value_date=date(2026, 5, 5),
        counterparty_lei="254900CUSTBANK000001",
        instrument_id="EURUSD",
        currency="USD",
        amount=Decimal("1000000"),
        fx_rate=Decimal("1.10000000"),
    )
    assert body.amount == Decimal("1000000")
    assert body.currency == "USD"
    assert body.instrument_id == "EURUSD"


def test_cancel_event_request_does_not_require_amended_fields() -> None:
    """FR-08: CANCEL events carry no field amendments."""
    body = TradeEventCreateRequest(
        event_type="CANCEL",
        reason="Trade cancelled by counterparty",
        requested_by="fo_user_01",
    )
    assert body.event_type == "CANCEL"
    assert body.amended_fields is None


def test_amend_event_request_with_amended_fields_is_valid() -> None:
    """FR-08: AMEND events with amended_fields pass schema validation."""
    body = TradeEventCreateRequest(
        event_type="AMEND",
        reason="Correct value date",
        requested_by="fo_user_01",
        amended_fields={"value_date": "2026-05-10", "fx_rate": "1.09250000"},
    )
    assert body.amended_fields == {"value_date": "2026-05-10", "fx_rate": "1.09250000"}


def test_trade_out_amount_and_fx_rate_are_strings() -> None:
    """Amount and fx_rate serialize as strings to preserve decimal precision."""
    from src.presentation.schemas import TradeOut

    out = TradeOut(
        trade_id="TRD-001",
        version=1,
        workflow_status="Initial",
        is_current=True,
        counterparty_lei="254900CUSTBANK000001",
        instrument_id="EURUSD",
        currency="USD",
        amount="1000000.00000000",
        fx_rate="1.10000000",
        trade_type="Spot",
        value_date=date(2026, 5, 5),
        trade_date=date(2026, 5, 1),
        input_date=date(2026, 5, 1),
        settlement_currency="USD",
    )
    assert isinstance(out.amount, str)
    assert isinstance(out.fx_rate, str)
