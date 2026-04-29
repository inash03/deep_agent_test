"""Rule list endpoint — returns FO and BO rule definitions."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


class RuleOut(BaseModel):
    rule_name: str
    severity: str
    check_type: str
    description: str
    is_stub: bool


class RuleListResponse(BaseModel):
    fo_rules: list[RuleOut]
    bo_rules: list[RuleOut]


_FO_RULES: list[RuleOut] = [
    RuleOut(
        rule_name="trade_date_not_future",
        severity="error",
        check_type="FO",
        description="Ensures the trade date is not in the future. A future trade date likely indicates a data entry error.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="trade_date_not_weekend",
        severity="error",
        check_type="FO",
        description="Ensures the trade date falls on a weekday (Monday–Friday). FX markets operate on business days only.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_after_trade_date",
        severity="error",
        check_type="FO",
        description="Ensures the value date is strictly after the trade date.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_not_past",
        severity="error",
        check_type="FO",
        description="Ensures the value date is not earlier than today. A past value date cannot be settled.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="value_date_settlement_cycle",
        severity="warning",
        check_type="FO",
        description="Ensures the value date is at least T+2 from the trade date, conforming to the standard FX settlement cycle (SWIFT convention).",
        is_stub=False,
    ),
    RuleOut(
        rule_name="amount_positive",
        severity="error",
        check_type="FO",
        description="Ensures the trade amount is greater than zero. A zero or negative amount is invalid.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="settlement_currency_consistency",
        severity="error",
        check_type="FO",
        description="Ensures the settlement currency appears within the instrument ID (e.g. EURUSD). Validates alignment between the currency pair and the settlement currency.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="counterparty_exists",
        severity="error",
        check_type="FO",
        description="Counterparty existence check (stub). Actual validation is performed by the BoCheck counterparty_exists rule.",
        is_stub=True,
    ),
    RuleOut(
        rule_name="instrument_exists",
        severity="error",
        check_type="FO",
        description="Instrument existence check (stub). Actual validation is performed at BoCheck.",
        is_stub=True,
    ),
]

_BO_RULES: list[RuleOut] = [
    RuleOut(
        rule_name="counterparty_exists",
        severity="error",
        check_type="BO",
        description="Ensures the counterparty LEI is registered in master data.",
        is_stub=False,
    ),
    RuleOut(
        rule_name="counterparty_active",
        severity="error",
        check_type="BO",
        description="Ensures the counterparty is currently active. Transactions with inactive counterparties are rejected (equivalent to SWIFT AG01).",
        is_stub=False,
    ),
    RuleOut(
        rule_name="ssi_exists",
        severity="error",
        check_type="BO",
        description="Ensures an internal SSI (Settlement Standing Instruction) is registered for the given LEI and currency. A missing SSI prevents settlement (equivalent to SWIFT AC01).",
        is_stub=False,
    ),
    RuleOut(
        rule_name="bic_format_valid",
        severity="error",
        check_type="BO",
        description="Ensures the BIC code in the SSI is either 8 or 11 characters long (SWIFT standard).",
        is_stub=False,
    ),
    RuleOut(
        rule_name="iban_format_valid",
        severity="error",
        check_type="BO",
        description="Ensures the IBAN in the SSI conforms to the international standard format [A-Z]{2}[0-9]{2}[A-Z0-9]{1,30} (equivalent to SWIFT BE01).",
        is_stub=False,
    ),
    RuleOut(
        rule_name="risk_limit_check",
        severity="error",
        check_type="BO",
        description="Ensures the trade amount is within the counterparty's risk limit (stub — always passes).",
        is_stub=True,
    ),
    RuleOut(
        rule_name="compliance_check",
        severity="error",
        check_type="BO",
        description="Ensures the counterparty meets sanctions list and compliance requirements (stub — always passes).",
        is_stub=True,
    ),
    RuleOut(
        rule_name="settlement_confirmed",
        severity="error",
        check_type="BO",
        description="Confirms that SWIFT settlement confirmation was received (stub). Pre-seeded bo_check_results can simulate AC01 / AM04 / SLA timeout rejection scenarios.",
        is_stub=True,
    ),
]


@router.get("", response_model=RuleListResponse)
def list_rules() -> RuleListResponse:
    return RuleListResponse(fo_rules=_FO_RULES, bo_rules=_BO_RULES)
