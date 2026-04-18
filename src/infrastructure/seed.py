"""Seed data for the STP Exception Triage Agent.

Populates the DB with demo data:
  - 5 STP_FAILED trades (TRD-001〜005): basic scenarios
  - 5 STP_FAILED trades (TRD-008〜012): complex/ambiguous SWIFT scenarios (Phase 24-B)
  - 2 NEW trades (TRD-006〜007) for the "create exception" demo
  - 6 counterparties (incl. 1 inactive), 4 reference data instruments
  - 6 internal SSIs + 1 external SSI

Usage:
  python -m src.infrastructure.seed       # run as module (idempotent seed)
  python -m src.infrastructure.seed reset  # truncate and re-seed
"""

from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.infrastructure.db.models import (
    CounterpartyModel,
    ReferenceDataModel,
    SettlementInstructionModel,
    StpExceptionModel,
    TradeModel,
)
from src.infrastructure.db.session import make_session

_TRADE_DATE = date(2026, 4, 1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Insert helpers
# ---------------------------------------------------------------------------


def _insert_counterparties(db: Session) -> None:
    db.add_all([
        CounterpartyModel(
            lei="213800QILIUD4ROSUO03", name="Acme Bank Ltd",
            bic="ACMEGB2L", is_active=True,
            created_at=_now(), updated_at=_now(),
        ),
        CounterpartyModel(
            lei="5493001KJTIIGC8Y1R12", name="Global Securities Inc",
            bic="GLSBUS33", is_active=True,
            created_at=_now(), updated_at=_now(),
        ),
        CounterpartyModel(
            lei="9695005MSX1OYEMGDF46", name="Pacific Finance Corp",
            bic="PACFJPJT", is_active=True,
            created_at=_now(), updated_at=_now(),
        ),
        # Phase 24-B: inactive counterparty (AG01 scenario)
        CounterpartyModel(
            lei="213800XYZINACTIVE001", name="Zenith Trading Corp",
            bic="ZNTHGB2L", is_active=False,
            created_at=_now(), updated_at=_now(),
        ),
        # Phase 24-B: custodian rejection scenario
        CounterpartyModel(
            lei="254900CUSTBANK000001", name="Metro Custody Bank",
            bic="MTCUBS33", is_active=True,
            created_at=_now(), updated_at=_now(),
        ),
        # Phase 24-B: expired BIC scenario
        CounterpartyModel(
            lei="529900ATLANTIC000001", name="Atlantic Finance Ltd",
            bic="ATLCGB2L", is_active=True,
            created_at=_now(), updated_at=_now(),
        ),
    ])


def _insert_reference_data(db: Session) -> None:
    db.add_all([
        ReferenceDataModel(
            instrument_id="USDJPY", description="US Dollar / Japanese Yen",
            asset_class="FX", is_active=True, created_at=_now(), updated_at=_now(),
        ),
        ReferenceDataModel(
            instrument_id="EURUSD", description="Euro / US Dollar",
            asset_class="FX", is_active=True, created_at=_now(), updated_at=_now(),
        ),
        ReferenceDataModel(
            instrument_id="GBPUSD", description="British Pound / US Dollar",
            asset_class="FX", is_active=True, created_at=_now(), updated_at=_now(),
        ),
        ReferenceDataModel(
            instrument_id="AUDUSD", description="Australian Dollar / US Dollar",
            asset_class="FX", is_active=True, created_at=_now(), updated_at=_now(),
        ),
    ])


def _insert_ssis(db: Session) -> None:
    db.add_all([
        # TRD-002: malformed BIC (BIC_FORMAT_ERROR — 9 chars, must be 8 or 11)
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="5493001KJTIIGC8Y1R12", currency="EUR",
            bic="GLSBUSS33", account="DE89370400440532013000",
            iban="DE89370400440532013000", is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-004: valid internal SSI
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="9695005MSX1OYEMGDF46", currency="AUD",
            bic="PACFJPJT", account="AU12345678901234",
            iban=None, is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-005: valid internal SSI
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="9695005MSX1OYEMGDF46", currency="USD",
            bic="PACFJPJT", account="US12345678901234",
            iban=None, is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-001: external SSI (MISSING_SSI — triggers HITL)
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="213800QILIUD4ROSUO03", currency="USD",
            bic="ACMEGB2L", account="GB29NWBK60161331926819",
            iban="GB29NWBK60161331926819", is_external=True,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-008: Acme/EUR internal SSI with outdated account number (AC01)
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="213800QILIUD4ROSUO03", currency="EUR",
            bic="ACMEGB2L", account="GB29NWBK60161331000000",
            iban="GB29NWBK60161331000000", is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-011: Metro Custody Bank/GBP with malformed IBAN
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="254900CUSTBANK000001", currency="GBP",
            bic="MTCUBS33", account="GBXX-INVALID-IBAN-9999",
            iban="GBXX-INVALID-IBAN-9999", is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
        # TRD-012: Atlantic Finance/JPY with expired BIC
        SettlementInstructionModel(
            id=uuid.uuid4(), lei="529900ATLANTIC000001", currency="JPY",
            bic="ATLCGB2LXXX", account="AT483200000012345864",
            iban=None, is_external=False,
            created_at=_now(), updated_at=_now(),
        ),
    ])


def _insert_trades_and_exceptions(db: Session) -> None:
    # (trade_id, cp_lei, instrument, currency, amount, value_date, settlement_ccy, stp_status, error_message)
    failed = [
        (
            "TRD-001", "213800QILIUD4ROSUO03", "USDJPY", "USD",
            Decimal("1000000.00"), date(2026, 4, 8), "USD", "STP_FAILED",
            "SSI not registered for counterparty 213800QILIUD4ROSUO03 / USD",
        ),
        (
            "TRD-002", "5493001KJTIIGC8Y1R12", "EURUSD", "EUR",
            Decimal("500000.00"), date(2026, 4, 8), "EUR", "STP_FAILED",
            "Invalid BIC format in settlement instructions for 5493001KJTIIGC8Y1R12 / EUR",
        ),
        (
            "TRD-003", "UNKNOWNLEI000000001", "GBPUSD", "GBP",
            Decimal("250000.00"), date(2026, 4, 8), "GBP", "STP_FAILED",
            "Counterparty LEI UNKNOWNLEI000000001 not found in master data",
        ),
        (
            "TRD-004", "9695005MSX1OYEMGDF46", "AUDUSD", "AUD",
            Decimal("750000.00"), date(2024, 1, 1), "AUD", "STP_FAILED",
            "Value date 2024-01-01 is in the past",
        ),
        (
            "TRD-005", "9695005MSX1OYEMGDF46", "UNKNOWN_CCY_PAIR", "USD",
            Decimal("100000.00"), date(2026, 4, 8), "USD", "STP_FAILED",
            "Instrument UNKNOWN_CCY_PAIR not found in reference data",
        ),
    ]
    # Phase 24-B: complex/ambiguous SWIFT scenarios (TRD-008〜012)
    complex_failed = [
        (
            "TRD-008", "213800QILIUD4ROSUO03", "EURUSD", "EUR",
            Decimal("800000.00"), date(2026, 4, 8), "EUR", "STP_FAILED",
            "MT103 rejected by SWIFT. Reason code: AC01. Sender BIC: ACMEGB2L.",
        ),
        (
            "TRD-009", "213800XYZINACTIVE001", "USDJPY", "USD",
            Decimal("1200000.00"), date(2026, 4, 8), "USD", "STP_FAILED",
            "MT103 rejected by SWIFT. Reason code: AG01. Counterparty LEI: 213800XYZINACTIVE001.",
        ),
        (
            "TRD-010", "213800XYZINACTIVE001", "GBPUSD", "GBP",
            Decimal("600000.00"), date(2026, 4, 8), "GBP", "STP_FAILED",
            "Pre-settlement validation failed for TRD-010. Multiple checks not passed.",
        ),
        (
            "TRD-011", "254900CUSTBANK000001", "GBPUSD", "GBP",
            Decimal("450000.00"), date(2026, 4, 8), "GBP", "STP_FAILED",
            "Custodian HSBC rejected settlement instruction for TRD-011. No further details provided.",
        ),
        (
            "TRD-012", "529900ATLANTIC000001", "USDJPY", "JPY",
            Decimal("90000000.00"), date(2026, 4, 8), "JPY", "STP_FAILED",
            "Settlement confirmation not received within SLA window for TRD-012. Status unknown.",
        ),
    ]
    for row in complex_failed:
        trade_id, cp_lei, instr, ccy, amt, vd, sc, status, err = row
        db.add(TradeModel(
            trade_id=trade_id, counterparty_lei=cp_lei, instrument_id=instr,
            currency=ccy, amount=amt, value_date=vd, trade_date=_TRADE_DATE,
            settlement_currency=sc, stp_status=status,
            created_at=_now(), updated_at=_now(),
        ))
        db.add(StpExceptionModel(
            id=uuid.uuid4(), trade_id=trade_id, error_message=err,
            status="OPEN", triage_run_id=None,
            created_at=_now(), updated_at=_now(),
        ))

    # NEW status trades for the "create exception" demo (no exceptions yet)
    new_trades = [
        (
            "TRD-006", "213800QILIUD4ROSUO03", "EURUSD", "EUR",
            Decimal("200000.00"), date(2026, 4, 20), "EUR", "NEW",
        ),
        (
            "TRD-007", "9695005MSX1OYEMGDF46", "GBPUSD", "GBP",
            Decimal("350000.00"), date(2026, 4, 20), "GBP", "NEW",
        ),
    ]

    for row in failed:
        trade_id, cp_lei, instr, ccy, amt, vd, sc, status, err = row
        db.add(TradeModel(
            trade_id=trade_id, counterparty_lei=cp_lei, instrument_id=instr,
            currency=ccy, amount=amt, value_date=vd, trade_date=_TRADE_DATE,
            settlement_currency=sc, stp_status=status,
            created_at=_now(), updated_at=_now(),
        ))
        db.add(StpExceptionModel(
            id=uuid.uuid4(), trade_id=trade_id, error_message=err,
            status="OPEN", triage_run_id=None,
            created_at=_now(), updated_at=_now(),
        ))

    for trade_id, cp_lei, instr, ccy, amt, vd, sc, status in new_trades:
        db.add(TradeModel(
            trade_id=trade_id, counterparty_lei=cp_lei, instrument_id=instr,
            currency=ccy, amount=amt, value_date=vd, trade_date=_TRADE_DATE,
            settlement_currency=sc, stp_status=status,
            created_at=_now(), updated_at=_now(),
        ))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def seed_database(db: Session) -> None:
    """Idempotent seed — skips if trades table already has rows."""
    if db.query(TradeModel).count() > 0:
        return
    _insert_counterparties(db)
    _insert_reference_data(db)
    _insert_ssis(db)
    _insert_trades_and_exceptions(db)
    db.commit()
    print("[seed] initial data inserted.")


def reset_and_seed(db: Session) -> None:
    """Truncate all domain tables (preserves triage history) and re-seed."""
    db.execute(text(
        "TRUNCATE TABLE stp_exceptions, settlement_instructions, "
        "reference_data, counterparties, trades RESTART IDENTITY"
    ))
    db.commit()
    _insert_counterparties(db)
    _insert_reference_data(db)
    _insert_ssis(db)
    _insert_trades_and_exceptions(db)
    db.commit()
    print("[seed] data reset and re-seeded.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "seed"
    db = make_session()
    try:
        if mode == "reset":
            reset_and_seed(db)
        else:
            seed_database(db)
    finally:
        db.close()
