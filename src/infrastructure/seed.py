"""Seed data for the STP Exception Triage Agent.

Populates the DB with demo data:
  - 5 STP_FAILED trades (TRD-001〜005): basic scenarios
  - 5 STP_FAILED trades (TRD-008〜012): complex/ambiguous SWIFT scenarios (Phase 24-B)
  - 2 NEW trades (TRD-006〜007) for the "create exception" demo
  - 6 counterparties (incl. 1 inactive), 4 reference data instruments
  - 6 internal SSIs + 1 external SSI

Usage:
  python -m src.infrastructure.seed       # additive upsert (adds missing records only)
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
    AppSettingModel,
    CounterpartyModel,
    ReferenceDataModel,
    SettlementInstructionModel,
    StpExceptionModel,
    TradeModel,
)
from src.infrastructure.db.session import make_session
from src.infrastructure.db.trade_repository import TradeRepository

_TRADE_DATE = date(2026, 4, 1)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Insert helpers
# ---------------------------------------------------------------------------


_COUNTERPARTIES = [
    {"lei": "213800QILIUD4ROSUO03", "name": "Acme Bank Ltd",       "bic": "ACMEGB2L",  "is_active": True},
    {"lei": "5493001KJTIIGC8Y1R12", "name": "Global Securities Inc","bic": "GLSBUS33",  "is_active": True},
    {"lei": "9695005MSX1OYEMGDF46", "name": "Pacific Finance Corp", "bic": "PACFJPJT",  "is_active": True},
    {"lei": "213800XYZINACTIVE001", "name": "Zenith Trading Corp",  "bic": "ZNTHGB2L",  "is_active": False},
    {"lei": "254900CUSTBANK000001", "name": "Metro Custody Bank",   "bic": "MTCUBS33",  "is_active": True},
    {"lei": "529900ATLANTIC000001", "name": "Atlantic Finance Ltd", "bic": "ATLCGB2L",  "is_active": True},
]


def _upsert_counterparties(db: Session) -> None:
    existing = {lei for (lei,) in db.query(CounterpartyModel.lei)}
    for row in _COUNTERPARTIES:
        if row["lei"] not in existing:
            db.add(CounterpartyModel(**row, created_at=_now(), updated_at=_now()))


_REFERENCE_DATA = [
    {"instrument_id": "USDJPY", "description": "US Dollar / Japanese Yen",          "asset_class": "FX", "is_active": True},
    {"instrument_id": "EURUSD", "description": "Euro / US Dollar",                   "asset_class": "FX", "is_active": True},
    {"instrument_id": "GBPUSD", "description": "British Pound / US Dollar",          "asset_class": "FX", "is_active": True},
    {"instrument_id": "AUDUSD", "description": "Australian Dollar / US Dollar",      "asset_class": "FX", "is_active": True},
]


def _upsert_reference_data(db: Session) -> None:
    existing = {iid for (iid,) in db.query(ReferenceDataModel.instrument_id)}
    for row in _REFERENCE_DATA:
        if row["instrument_id"] not in existing:
            db.add(ReferenceDataModel(**row, created_at=_now(), updated_at=_now()))


# (lei, currency, is_external, bic, account, iban)
_SSIS = [
    ("5493001KJTIIGC8Y1R12", "EUR", False, "GLSBUSS33",  "DE89370400440532013000", "DE89370400440532013000"),
    ("9695005MSX1OYEMGDF46", "AUD", False, "PACFJPJT",   "AU12345678901234",        None),
    ("9695005MSX1OYEMGDF46", "USD", False, "PACFJPJT",   "US12345678901234",        None),
    ("213800QILIUD4ROSUO03", "USD", True,  "ACMEGB2L",   "GB29NWBK60161331926819", "GB29NWBK60161331926819"),
    ("213800QILIUD4ROSUO03", "EUR", False, "ACMEGB2L",   "GB29NWBK60161331000000", "GB29NWBK60161331000000"),
    ("254900CUSTBANK000001", "GBP", False, "MTCUBS33",   "GBXX-INVALID-IBAN-9999", "GBXX-INVALID-IBAN-9999"),
    ("529900ATLANTIC000001", "JPY", False, "ATLCGB2LXXX","AT483200000012345864",    None),
    # Registered when Zenith Trading Corp was active; remains in DB after deactivation
    ("213800XYZINACTIVE001", "USD", False, "ZNTHGB2L",   "US12345678901234",        None),
]


def _upsert_ssis(db: Session) -> None:
    existing = {
        (lei, ccy, ext)
        for lei, ccy, ext in db.query(
            SettlementInstructionModel.lei,
            SettlementInstructionModel.currency,
            SettlementInstructionModel.is_external,
        )
    }
    for lei, ccy, is_ext, bic, account, iban in _SSIS:
        if (lei, ccy, is_ext) not in existing:
            db.add(SettlementInstructionModel(
                id=uuid.uuid4(), lei=lei, currency=ccy, is_external=is_ext,
                bic=bic, account=account, iban=iban,
                created_at=_now(), updated_at=_now(),
            ))


_APP_SETTINGS = [
    {
        "key": "fo_check_trigger",
        "value": "manual",
        "description": "Trigger mode for FoCheck: auto (run on Initial entry) or manual",
    },
    {
        "key": "bo_check_trigger",
        "value": "manual",
        "description": "Trigger mode for BoCheck: auto (run on FoValidated entry) or manual",
    },
    {
        "key": "fo_triage_trigger",
        "value": "manual",
        "description": "Trigger mode for FoTriage: auto (run after FoCheck failure) or manual",
    },
    {
        "key": "bo_triage_trigger",
        "value": "manual",
        "description": "Trigger mode for BoTriage: auto (run after BoCheck failure) or manual",
    },
]


def _upsert_app_settings(db: Session) -> None:
    existing = {key for (key,) in db.query(AppSettingModel.key)}
    for row in _APP_SETTINGS:
        if row["key"] not in existing:
            db.add(AppSettingModel(**row, updated_at=_now()))


# ---------------------------------------------------------------------------
# Pre-computed check results
# ---------------------------------------------------------------------------


def _fo_all_pass() -> list[dict]:
    """FoCheck results for a trade where all FO rules passed."""
    return [
        {"rule_name": "trade_date_not_future",           "passed": True, "severity": "error",   "message": f"Trade date {_TRADE_DATE} is not in the future"},
        {"rule_name": "trade_date_not_weekend",          "passed": True, "severity": "error",   "message": f"Trade date {_TRADE_DATE} is a business day"},
        {"rule_name": "value_date_after_trade_date",     "passed": True, "severity": "error",   "message": "Value date 2026-04-08 is after trade date 2026-04-01"},
        {"rule_name": "value_date_not_past",             "passed": True, "severity": "error",   "message": "Value date 2026-04-08 is not in the past"},
        {"rule_name": "value_date_settlement_cycle",     "passed": True, "severity": "warning", "message": "Value date 2026-04-08 meets T+2 settlement cycle"},
        {"rule_name": "amount_positive",                 "passed": True, "severity": "error",   "message": "Amount is positive"},
        {"rule_name": "settlement_currency_consistency", "passed": True, "severity": "error",   "message": "Settlement currency is consistent with instrument"},
        {"rule_name": "counterparty_exists",             "passed": True, "severity": "error",   "message": "Counterparty pre-check skipped (stub; validated at BoCheck)"},
        {"rule_name": "instrument_exists",               "passed": True, "severity": "error",   "message": "Instrument pre-check skipped (stub; validated at BoCheck)"},
    ]


# TRD-004: value_date=2024-01-01 predates trade_date=2026-04-01 and is in the past
_TRD_004_FO_RESULTS: list[dict] = [
    {"rule_name": "trade_date_not_future",           "passed": True,  "severity": "error",   "message": f"Trade date {_TRADE_DATE} is not in the future"},
    {"rule_name": "trade_date_not_weekend",          "passed": True,  "severity": "error",   "message": f"Trade date {_TRADE_DATE} is a business day"},
    {"rule_name": "value_date_after_trade_date",     "passed": False, "severity": "error",   "message": "Value date 2024-01-01 must be strictly after trade date 2026-04-01"},
    {"rule_name": "value_date_not_past",             "passed": False, "severity": "error",   "message": "Value date 2024-01-01 is in the past (today: 2026-04-01)"},
    {"rule_name": "value_date_settlement_cycle",     "passed": False, "severity": "warning", "message": "Value date 2024-01-01 is earlier than T+2 (2026-04-03) — FX standard settlement cycle"},
    {"rule_name": "amount_positive",                 "passed": True,  "severity": "error",   "message": "Amount 750000.00 is positive"},
    {"rule_name": "settlement_currency_consistency", "passed": True,  "severity": "error",   "message": "Settlement currency 'AUD' is consistent with instrument 'AUDUSD'"},
    {"rule_name": "counterparty_exists",             "passed": True,  "severity": "error",   "message": "Counterparty pre-check skipped (stub; validated at BoCheck)"},
    {"rule_name": "instrument_exists",               "passed": True,  "severity": "error",   "message": "Instrument pre-check skipped (stub; validated at BoCheck)"},
]

# TRD-005: instrument=UNKNOWN_CCY_PAIR — settlement currency mismatch + unknown instrument
_TRD_005_FO_RESULTS: list[dict] = [
    {"rule_name": "trade_date_not_future",           "passed": True,  "severity": "error",   "message": f"Trade date {_TRADE_DATE} is not in the future"},
    {"rule_name": "trade_date_not_weekend",          "passed": True,  "severity": "error",   "message": f"Trade date {_TRADE_DATE} is a business day"},
    {"rule_name": "value_date_after_trade_date",     "passed": True,  "severity": "error",   "message": "Value date 2026-04-08 is after trade date 2026-04-01"},
    {"rule_name": "value_date_not_past",             "passed": True,  "severity": "error",   "message": "Value date 2026-04-08 is not in the past"},
    {"rule_name": "value_date_settlement_cycle",     "passed": True,  "severity": "warning", "message": "Value date 2026-04-08 meets T+2 settlement cycle"},
    {"rule_name": "amount_positive",                 "passed": True,  "severity": "error",   "message": "Amount 100000.00 is positive"},
    {"rule_name": "settlement_currency_consistency", "passed": False, "severity": "error",   "message": "Settlement currency 'USD' does not appear in instrument 'UNKNOWN_CCY_PAIR'"},
    {"rule_name": "counterparty_exists",             "passed": True,  "severity": "error",   "message": "Counterparty pre-check skipped (stub; validated at BoCheck)"},
    {"rule_name": "instrument_exists",               "passed": False, "severity": "error",   "message": "Instrument 'UNKNOWN_CCY_PAIR' not found in reference data"},
]


# TRD-001: ssi_exists fails — no internal SSI for 213800QILIUD4ROSUO03 / USD (only external)
_TRD_001_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '213800QILIUD4ROSUO03' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '213800QILIUD4ROSUO03' is active"},
    {"rule_name": "ssi_exists",           "passed": False, "severity": "error",   "message": "No internal SSI registered for LEI '213800QILIUD4ROSUO03' / currency 'USD'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "No SSI present — BIC check skipped"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]

# TRD-002: bic_format_valid fails — BIC 'GLSBUSS33' is 9 chars (must be 8 or 11)
_TRD_002_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '5493001KJTIIGC8Y1R12' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '5493001KJTIIGC8Y1R12' is active"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '5493001KJTIIGC8Y1R12' / currency 'EUR'"},
    {"rule_name": "bic_format_valid",     "passed": False, "severity": "error",   "message": "BIC 'GLSBUSS33' must be 8 or 11 characters (actual: 9)"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "IBAN 'DE89370400440532013000' has valid format"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]

# TRD-003: counterparty_exists / active / ssi_exists all fail — unknown LEI → COMPOUND
_TRD_003_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": False, "severity": "error",   "message": "Counterparty LEI 'UNKNOWNLEI000000001' not found in master data"},
    {"rule_name": "counterparty_active",  "passed": False, "severity": "error",   "message": "Counterparty not found — cannot verify active status"},
    {"rule_name": "ssi_exists",           "passed": False, "severity": "error",   "message": "No internal SSI registered for LEI 'UNKNOWNLEI000000001' / currency 'GBP'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "No SSI present — BIC check skipped"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]


# TRD-008: settlement_confirmed fails — SWIFT AC01 rejection (internal SSI format valid)
_TRD_008_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '213800QILIUD4ROSUO03' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '213800QILIUD4ROSUO03' is active"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '213800QILIUD4ROSUO03' / currency 'EUR'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "BIC 'ACMEGB2L' has valid length (8 chars)"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "IBAN 'GB29NWBK60161331000000' has valid format"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": False, "severity": "error",   "message": "MT103 rejected by SWIFT: AC01 — incorrect account number. Sender BIC: ACMEGB2L."},
]

# TRD-009: counterparty_active fails — AG01 (inactive CP; USD SSI still registered)
_TRD_009_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '213800XYZINACTIVE001' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": False, "severity": "error",   "message": "Counterparty '213800XYZINACTIVE001' (Zenith Trading Corp) is inactive"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '213800XYZINACTIVE001' / currency 'USD'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "BIC 'ZNTHGB2L' has valid length (8 chars)"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]

# TRD-010: counterparty_active + ssi_exists both fail — COMPOUND (inactive CP, no GBP SSI)
_TRD_010_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '213800XYZINACTIVE001' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": False, "severity": "error",   "message": "Counterparty '213800XYZINACTIVE001' (Zenith Trading Corp) is inactive"},
    {"rule_name": "ssi_exists",           "passed": False, "severity": "error",   "message": "No internal SSI registered for LEI '213800XYZINACTIVE001' / currency 'GBP'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "No SSI present — BIC check skipped"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]

# TRD-011: iban_format_valid fails — BE01 (GBXX-INVALID-IBAN-9999 contains hyphens)
_TRD_011_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '254900CUSTBANK000001' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '254900CUSTBANK000001' is active"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '254900CUSTBANK000001' / currency 'GBP'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "BIC 'MTCUBS33' has valid length (8 chars)"},
    {"rule_name": "iban_format_valid",    "passed": False, "severity": "error",   "message": "IBAN 'GBXX-INVALID-IBAN-9999' does not match [A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": True,  "severity": "error",   "message": "Settlement confirmation stub — always passes"},
]

# TRD-012: settlement_confirmed fails — SLA exceeded, BIC may be expired → UNKNOWN
_TRD_012_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '529900ATLANTIC000001' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '529900ATLANTIC000001' is active"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '529900ATLANTIC000001' / currency 'JPY'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "BIC 'ATLCGB2LXXX' has valid length (11 chars)"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": False, "severity": "error",   "message": "Settlement confirmation not received within SLA window. BIC ATLCGB2LXXX may be expired."},
]

# TRD-013: settlement_confirmed fails — SWIFT AM04 (FO liquidity shortfall)
_TRD_013_BO_RESULTS: list[dict] = [
    {"rule_name": "counterparty_exists",  "passed": True,  "severity": "error",   "message": "Counterparty '9695005MSX1OYEMGDF46' exists in master data"},
    {"rule_name": "counterparty_active",  "passed": True,  "severity": "error",   "message": "Counterparty '9695005MSX1OYEMGDF46' is active"},
    {"rule_name": "ssi_exists",           "passed": True,  "severity": "error",   "message": "Internal SSI found for LEI '9695005MSX1OYEMGDF46' / currency 'USD'"},
    {"rule_name": "bic_format_valid",     "passed": True,  "severity": "error",   "message": "BIC 'PACFJPJT' has valid length (8 chars)"},
    {"rule_name": "iban_format_valid",    "passed": True,  "severity": "error",   "message": "No IBAN to validate"},
    {"rule_name": "risk_limit_check",     "passed": True,  "severity": "error",   "message": "Risk limit check passed (stub — always passes)"},
    {"rule_name": "compliance_check",     "passed": True,  "severity": "error",   "message": "Compliance / sanctions check passed (stub — always passes)"},
    {"rule_name": "settlement_confirmed", "passed": False, "severity": "error",   "message": "MT103 rejected by SWIFT: AM04 — insufficient funds at correspondent bank. FO liquidity shortfall."},
]


def _upsert_trades_and_exceptions(db: Session) -> None:
    existing_trades = {tid for (tid,) in db.query(TradeModel.trade_id)}
    existing_exc_trades = {tid for (tid,) in db.query(StpExceptionModel.trade_id)}

    # ------------------------------------------------------------------
    # FO-failing trades — FoCheck ran and found FO-level errors
    # workflow_status=FoAgentToCheck; fo_check_results populated
    # ------------------------------------------------------------------
    fo_failing = [
        {
            "trade_id": "TRD-004",
            "cp_lei": "9695005MSX1OYEMGDF46", "instr": "AUDUSD", "ccy": "AUD",
            "amt": Decimal("750000.00"), "vd": date(2024, 1, 1), "sc": "AUD",
            "err": "Value date 2024-01-01 is in the past",
            "fo_results": _TRD_004_FO_RESULTS,
        },
        {
            "trade_id": "TRD-005",
            "cp_lei": "9695005MSX1OYEMGDF46", "instr": "UNKNOWN_CCY_PAIR", "ccy": "USD",
            "amt": Decimal("100000.00"), "vd": date(2026, 4, 8), "sc": "USD",
            "err": "Instrument UNKNOWN_CCY_PAIR not found in reference data",
            "fo_results": _TRD_005_FO_RESULTS,
        },
    ]

    for t in fo_failing:
        if t["trade_id"] not in existing_trades:
            db.add(TradeModel(
                trade_id=t["trade_id"], version=1, is_current=True,
                workflow_status="FoAgentToCheck",
                counterparty_lei=t["cp_lei"], instrument_id=t["instr"],
                currency=t["ccy"], amount=t["amt"],
                value_date=t["vd"], trade_date=_TRADE_DATE,
                settlement_currency=t["sc"],
                sendback_count=0,
                fo_check_results=t["fo_results"],
                created_at=_now(), updated_at=_now(),
            ))
        if t["trade_id"] not in existing_exc_trades:
            db.add(StpExceptionModel(
                id=uuid.uuid4(), trade_id=t["trade_id"], error_message=t["err"],
                status="OPEN", triage_run_id=None,
                created_at=_now(), updated_at=_now(),
            ))

    # ------------------------------------------------------------------
    # BO-failing trades — FoCheck passed, BoCheck found errors
    # workflow_status=BoAgentToCheck; both fo_ and bo_check_results populated
    # ------------------------------------------------------------------
    bo_failing = [
        {
            "trade_id": "TRD-001",
            "cp_lei": "213800QILIUD4ROSUO03", "instr": "USDJPY", "ccy": "USD",
            "amt": Decimal("1000000.00"), "vd": date(2026, 4, 8), "sc": "USD",
            "err": "SSI not registered for counterparty 213800QILIUD4ROSUO03 / USD",
            "bo_results": _TRD_001_BO_RESULTS,
        },
        {
            "trade_id": "TRD-002",
            "cp_lei": "5493001KJTIIGC8Y1R12", "instr": "EURUSD", "ccy": "EUR",
            "amt": Decimal("500000.00"), "vd": date(2026, 4, 8), "sc": "EUR",
            "err": "Invalid BIC format in settlement instructions for 5493001KJTIIGC8Y1R12 / EUR",
            "bo_results": _TRD_002_BO_RESULTS,
        },
        {
            "trade_id": "TRD-003",
            "cp_lei": "UNKNOWNLEI000000001", "instr": "GBPUSD", "ccy": "GBP",
            "amt": Decimal("250000.00"), "vd": date(2026, 4, 8), "sc": "GBP",
            "err": "Counterparty LEI UNKNOWNLEI000000001 not found in master data",
            "bo_results": _TRD_003_BO_RESULTS,
        },
        {
            "trade_id": "TRD-008",
            "cp_lei": "213800QILIUD4ROSUO03", "instr": "EURUSD", "ccy": "EUR",
            "amt": Decimal("800000.00"), "vd": date(2026, 4, 8), "sc": "EUR",
            "err": "MT103 rejected by SWIFT. Reason code: AC01. Sender BIC: ACMEGB2L.",
            "bo_results": _TRD_008_BO_RESULTS,
        },
        {
            "trade_id": "TRD-009",
            "cp_lei": "213800XYZINACTIVE001", "instr": "USDJPY", "ccy": "USD",
            "amt": Decimal("1200000.00"), "vd": date(2026, 4, 8), "sc": "USD",
            "err": "MT103 rejected by SWIFT. Reason code: AG01. Counterparty LEI: 213800XYZINACTIVE001.",
            "bo_results": _TRD_009_BO_RESULTS,
        },
        {
            "trade_id": "TRD-010",
            "cp_lei": "213800XYZINACTIVE001", "instr": "GBPUSD", "ccy": "GBP",
            "amt": Decimal("600000.00"), "vd": date(2026, 4, 8), "sc": "GBP",
            "err": "Pre-settlement validation failed for TRD-010. Multiple checks not passed.",
            "bo_results": _TRD_010_BO_RESULTS,
        },
        {
            "trade_id": "TRD-011",
            "cp_lei": "254900CUSTBANK000001", "instr": "GBPUSD", "ccy": "GBP",
            "amt": Decimal("450000.00"), "vd": date(2026, 4, 8), "sc": "GBP",
            "err": "Custodian HSBC rejected settlement instruction for TRD-011. No further details provided.",
            "bo_results": _TRD_011_BO_RESULTS,
        },
        {
            "trade_id": "TRD-012",
            "cp_lei": "529900ATLANTIC000001", "instr": "USDJPY", "ccy": "JPY",
            "amt": Decimal("90000000.00"), "vd": date(2026, 4, 8), "sc": "JPY",
            "err": "Settlement confirmation not received within SLA window for TRD-012. Status unknown.",
            "bo_results": _TRD_012_BO_RESULTS,
        },
    ]

    fo_pass = _fo_all_pass()
    for t in bo_failing:
        if t["trade_id"] not in existing_trades:
            db.add(TradeModel(
                trade_id=t["trade_id"], version=1, is_current=True,
                workflow_status="BoAgentToCheck",
                counterparty_lei=t["cp_lei"], instrument_id=t["instr"],
                currency=t["ccy"], amount=t["amt"],
                value_date=t["vd"], trade_date=_TRADE_DATE,
                settlement_currency=t["sc"],
                sendback_count=0,
                fo_check_results=fo_pass,
                bo_check_results=t["bo_results"],
                created_at=_now(), updated_at=_now(),
            ))
        if t["trade_id"] not in existing_exc_trades:
            db.add(StpExceptionModel(
                id=uuid.uuid4(), trade_id=t["trade_id"], error_message=t["err"],
                status="OPEN", triage_run_id=None,
                created_at=_now(), updated_at=_now(),
            ))

    # ------------------------------------------------------------------
    # Initial trades — no checks run yet
    # ------------------------------------------------------------------
    new_trades = [
        ("TRD-006", "213800QILIUD4ROSUO03", "EURUSD", "EUR", Decimal("200000.00"), date(2026, 4, 20), "EUR"),
        ("TRD-007", "9695005MSX1OYEMGDF46", "GBPUSD", "GBP", Decimal("350000.00"), date(2026, 4, 20), "GBP"),
    ]
    for trade_id, cp_lei, instr, ccy, amt, vd, sc in new_trades:
        if trade_id not in existing_trades:
            db.add(TradeModel(
                trade_id=trade_id, version=1, is_current=True,
                workflow_status="Initial",
                counterparty_lei=cp_lei, instrument_id=instr,
                currency=ccy, amount=amt, value_date=vd, trade_date=_TRADE_DATE,
                settlement_currency=sc,
                sendback_count=0,
                created_at=_now(), updated_at=_now(),
            ))

    # ------------------------------------------------------------------
    # TRD-013: AM04 — FO liquidity shortfall, all internal BO checks pass
    # ------------------------------------------------------------------
    if "TRD-013" not in existing_trades:
        db.add(TradeModel(
            trade_id="TRD-013", version=1, is_current=True,
            workflow_status="BoAgentToCheck",
            counterparty_lei="9695005MSX1OYEMGDF46", instrument_id="USDJPY",
            currency="USD", amount=Decimal("2000000.00"),
            value_date=date(2026, 5, 1), trade_date=_TRADE_DATE,
            settlement_currency="USD",
            sendback_count=0,
            fo_check_results=fo_pass,
            bo_check_results=_TRD_013_BO_RESULTS,
            created_at=_now(), updated_at=_now(),
        ))
    if "TRD-013" not in existing_exc_trades:
        db.add(StpExceptionModel(
            id=uuid.uuid4(), trade_id="TRD-013",
            error_message=(
                "MT103 rejected by SWIFT. Reason code: AM04. "
                "Insufficient funds at correspondent bank. FO liquidity shortfall."
            ),
            status="OPEN", triage_run_id=None,
            created_at=_now(), updated_at=_now(),
        ))


# ---------------------------------------------------------------------------
# Auto-trigger helper
# ---------------------------------------------------------------------------


def _maybe_auto_run_fo_check(db: Session) -> None:
    """If fo_check_trigger=auto, run FoCheck for all trades in Initial status.

    Called after seeding so that auto-mode deployments don't require a manual
    "Run FoCheck" click for every freshly seeded trade. This mirrors the same
    trigger semantics used by create_trade -> maybe_run_fo_check.
    """
    setting = db.query(AppSettingModel).filter(AppSettingModel.key == "fo_check_trigger").first()
    if not (setting and setting.value == "auto"):
        return

    # Import here to avoid circular dependency at module load time
    from src.infrastructure.rule_engine import run_fo_check  # noqa: PLC0415

    repo = TradeRepository(db)
    items, _ = repo.list(workflow_status="Initial", limit=100, offset=0)
    for trade in items:
        try:
            run_fo_check(trade.trade_id, db)
        except Exception as exc:  # noqa: BLE001
            print(f"[seed] auto FoCheck failed for {trade.trade_id}: {exc}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def seed_database(db: Session) -> None:
    """Additive upsert — inserts any seed records missing from the DB.

    Safe to run on every deploy: existing records (including user edits) are
    preserved; only records whose PK / unique key is absent are added.
    """
    _upsert_counterparties(db)
    _upsert_reference_data(db)
    _upsert_ssis(db)
    _upsert_trades_and_exceptions(db)
    _upsert_app_settings(db)
    db.commit()
    _maybe_auto_run_fo_check(db)
    print("[seed] seed data synced (missing records added).")


def reset_and_seed(db: Session) -> None:
    """Truncate all domain tables (preserves triage history) and re-seed."""
    db.execute(text(
        "TRUNCATE TABLE stp_exceptions, settlement_instructions, "
        "reference_data, counterparties, trades, app_settings RESTART IDENTITY"
    ))
    db.commit()
    _upsert_counterparties(db)
    _upsert_reference_data(db)
    _upsert_ssis(db)
    _upsert_trades_and_exceptions(db)
    _upsert_app_settings(db)
    db.commit()
    _maybe_auto_run_fo_check(db)
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
