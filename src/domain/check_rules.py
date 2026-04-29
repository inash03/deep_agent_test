"""Domain-layer rule definitions for FoCheck and BoCheck.

Rules are pure functions (no I/O). The rule_engine.py in the infrastructure
layer orchestrates DB lookups and calls these functions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.infrastructure.db.models import (
        CounterpartyModel,
        SettlementInstructionModel,
        TradeModel,
    )

_IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$")


# ---------------------------------------------------------------------------
# Rule type definitions
# ---------------------------------------------------------------------------


@dataclass
class FoRule:
    rule_name: str
    severity: str  # "error" | "warning"
    check_fn: Callable[["TradeModel"], tuple[bool, str]]


@dataclass
class BoRule:
    rule_name: str
    severity: str  # "error" | "warning"
    check_fn: Callable[
        [
            "TradeModel",
            "CounterpartyModel | None",
            "SettlementInstructionModel | None",
        ],
        tuple[bool, str],
    ]


# ---------------------------------------------------------------------------
# FoCheck rule implementations (pure — trade data only)
# ---------------------------------------------------------------------------


def _trade_date_not_future(trade: "TradeModel") -> tuple[bool, str]:
    today = date.today()
    if trade.trade_date > today:
        return False, f"Trade date {trade.trade_date} is in the future (today: {today})"
    return True, f"Trade date {trade.trade_date} is not in the future"


def _trade_date_not_weekend(trade: "TradeModel") -> tuple[bool, str]:
    wd = trade.trade_date.weekday()
    if wd >= 5:
        day_name = "Saturday" if wd == 5 else "Sunday"
        return False, f"Trade date {trade.trade_date} falls on a {day_name}"
    return True, f"Trade date {trade.trade_date} is a business day"


def _value_date_after_trade_date(trade: "TradeModel") -> tuple[bool, str]:
    if trade.value_date <= trade.trade_date:
        return False, (
            f"Value date {trade.value_date} must be strictly after "
            f"trade date {trade.trade_date}"
        )
    return True, f"Value date {trade.value_date} is after trade date {trade.trade_date}"


def _value_date_not_past(trade: "TradeModel") -> tuple[bool, str]:
    today = date.today()
    if trade.value_date < today:
        return False, f"Value date {trade.value_date} is in the past (today: {today})"
    return True, f"Value date {trade.value_date} is not in the past"


def _value_date_settlement_cycle(trade: "TradeModel") -> tuple[bool, str]:
    min_vd = trade.trade_date + timedelta(days=2)
    if trade.value_date < min_vd:
        return False, (
            f"Value date {trade.value_date} is earlier than T+2 ({min_vd}) — "
            "FX standard settlement cycle"
        )
    return True, f"Value date {trade.value_date} meets T+2 settlement cycle"


def _amount_positive(trade: "TradeModel") -> tuple[bool, str]:
    if trade.amount <= Decimal("0"):
        return False, f"Amount {trade.amount} must be greater than zero"
    return True, f"Amount {trade.amount} is positive"


def _settlement_currency_consistency(trade: "TradeModel") -> tuple[bool, str]:
    """Check that settlement currency appears as part of the instrument ID.

    Works for standard FX pair names (e.g. EURUSD, USDJPY, GBPUSD).
    """
    if trade.settlement_currency not in trade.instrument_id:
        return False, (
            f"Settlement currency {trade.settlement_currency!r} does not appear in "
            f"instrument {trade.instrument_id!r}"
        )
    return True, (
        f"Settlement currency {trade.settlement_currency!r} is consistent with "
        f"instrument {trade.instrument_id!r}"
    )


# Placeholder rules — always pass at runtime so existing logic is unaffected,
# but referenced by name in pre-seeded fo_check_results for demo scenarios that
# predate the FO/BO rule split.
def _counterparty_exists_fo(trade: "TradeModel") -> tuple[bool, str]:
    return True, f"Counterparty pre-check skipped (stub; validated at BoCheck)"


def _instrument_exists_fo(trade: "TradeModel") -> tuple[bool, str]:
    return True, f"Instrument pre-check skipped (stub; validated at BoCheck)"


FO_RULES: list[FoRule] = [
    FoRule("trade_date_not_future", "error", _trade_date_not_future),
    FoRule("trade_date_not_weekend", "error", _trade_date_not_weekend),
    FoRule("value_date_after_trade_date", "error", _value_date_after_trade_date),
    FoRule("value_date_not_past", "error", _value_date_not_past),
    FoRule("value_date_settlement_cycle", "warning", _value_date_settlement_cycle),
    FoRule("amount_positive", "error", _amount_positive),
    FoRule("settlement_currency_consistency", "error", _settlement_currency_consistency),
    FoRule("counterparty_exists", "error", _counterparty_exists_fo),
    FoRule("instrument_exists", "error", _instrument_exists_fo),
]


# ---------------------------------------------------------------------------
# BoCheck rule implementations (pre-fetched master data passed as args)
# ---------------------------------------------------------------------------


def _counterparty_exists(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    if cp is None:
        return False, f"Counterparty LEI {trade.counterparty_lei!r} not found in master data"
    return True, f"Counterparty {trade.counterparty_lei!r} exists in master data"


def _counterparty_active(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    if cp is None:
        return False, "Counterparty not found — cannot verify active status"
    if not cp.is_active:
        return False, f"Counterparty {trade.counterparty_lei!r} ({cp.name}) is inactive"
    return True, f"Counterparty {trade.counterparty_lei!r} is active"


def _ssi_exists(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    if ssi is None:
        return False, (
            f"No internal SSI registered for LEI {trade.counterparty_lei!r} / "
            f"currency {trade.currency!r}"
        )
    return True, (
        f"Internal SSI found for LEI {trade.counterparty_lei!r} / currency {trade.currency!r}"
    )


def _bic_format_valid(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    if ssi is None:
        return True, "No SSI present — BIC check skipped"
    bic = ssi.bic
    if len(bic) not in (8, 11):
        return False, (
            f"BIC {bic!r} must be 8 or 11 characters (actual: {len(bic)})"
        )
    return True, f"BIC {bic!r} has valid length ({len(bic)} chars)"


def _iban_format_valid(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    if ssi is None or ssi.iban is None:
        return True, "No IBAN to validate"
    if not _IBAN_RE.match(ssi.iban):
        return False, (
            f"IBAN {ssi.iban!r} does not match [A-Z]{{2}}[0-9]{{2}}[A-Z0-9]{{1,30}}"
        )
    return True, f"IBAN {ssi.iban!r} has valid format"


def _risk_limit_check(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    return True, "Risk limit check passed (stub — always passes)"


def _compliance_check(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    return True, "Compliance / sanctions check passed (stub — always passes)"


def _settlement_confirmed(
    trade: "TradeModel",
    cp: "CounterpartyModel | None",
    ssi: "SettlementInstructionModel | None",
) -> tuple[bool, str]:
    # Placeholder — always passes at runtime.
    # Pre-seeded bo_check_results can set this to False for SWIFT rejection scenarios
    # (AC01, AM04, SLA timeout) that are not detectable by internal data checks alone.
    return True, "Settlement confirmation stub — always passes"


BO_RULES: list[BoRule] = [
    BoRule("counterparty_exists", "error", _counterparty_exists),
    BoRule("counterparty_active", "error", _counterparty_active),
    BoRule("ssi_exists", "error", _ssi_exists),
    BoRule("bic_format_valid", "error", _bic_format_valid),
    BoRule("iban_format_valid", "error", _iban_format_valid),
    BoRule("risk_limit_check", "error", _risk_limit_check),
    BoRule("compliance_check", "error", _compliance_check),
    BoRule("settlement_confirmed", "error", _settlement_confirmed),
]
