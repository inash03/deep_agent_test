"""In-memory mock data store for the STP Exception Triage Agent.

Provides pre-populated test data covering the main failure scenarios:
  - TRD-001: MISSING_SSI  (SSI not registered; external lookup finds data → HITL)
  - TRD-002: BIC_FORMAT_ERROR (SSI exists but BIC has wrong format)
  - TRD-003: COUNTERPARTY_NOT_FOUND (LEI not in counterparty master)
  - TRD-004: INVALID_VALUE_DATE (value date is a holiday / past date)
  - TRD-005: INSTRUMENT_NOT_FOUND (instrument not in reference data)
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.domain.entities import (
    Counterparty,
    ReferenceData,
    SettlementInstruction,
    TradeDetail,
)

# ---------------------------------------------------------------------------
# Counterparty master
# ---------------------------------------------------------------------------

_COUNTERPARTIES: dict[str, Counterparty] = {
    "213800QILIUD4ROSUO03": Counterparty(
        lei="213800QILIUD4ROSUO03",
        name="Acme Bank Ltd",
        bic="ACMEGB2L",
        is_active=True,
    ),
    "5493001KJTIIGC8Y1R12": Counterparty(
        lei="5493001KJTIIGC8Y1R12",
        name="Global Securities Inc",
        bic="GLSBUS33",
        is_active=True,
    ),
    "9695005MSX1OYEMGDF46": Counterparty(
        lei="9695005MSX1OYEMGDF46",
        name="Pacific Finance Corp",
        bic="PACFJPJT",
        is_active=True,
    ),
    # TRD-003: LEI for counterparty that is NOT in master
    # "UNKNOWNLEI000000001" → intentionally absent
}

# ---------------------------------------------------------------------------
# Trade detail store
# ---------------------------------------------------------------------------

_TRADES: dict[str, TradeDetail] = {
    # TRD-001: MISSING_SSI — counterparty exists, but no SSI registered
    "TRD-001": TradeDetail(
        trade_id="TRD-001",
        counterparty_lei="213800QILIUD4ROSUO03",
        instrument_id="USDJPY",
        currency="USD",
        amount=Decimal("1000000.00"),
        value_date=date(2026, 4, 8),
        settlement_currency="USD",
    ),
    # TRD-002: BIC_FORMAT_ERROR — SSI exists but BIC is malformed (9 chars, not 8 or 11)
    "TRD-002": TradeDetail(
        trade_id="TRD-002",
        counterparty_lei="5493001KJTIIGC8Y1R12",
        instrument_id="EURUSD",
        currency="EUR",
        amount=Decimal("500000.00"),
        value_date=date(2026, 4, 8),
        settlement_currency="EUR",
    ),
    # TRD-003: COUNTERPARTY_NOT_FOUND — LEI not in master
    "TRD-003": TradeDetail(
        trade_id="TRD-003",
        counterparty_lei="UNKNOWNLEI000000001",
        instrument_id="GBPUSD",
        currency="GBP",
        amount=Decimal("250000.00"),
        value_date=date(2026, 4, 8),
        settlement_currency="GBP",
    ),
    # TRD-004: INVALID_VALUE_DATE — value date is in the past
    "TRD-004": TradeDetail(
        trade_id="TRD-004",
        counterparty_lei="9695005MSX1OYEMGDF46",
        instrument_id="AUDUSD",
        currency="AUD",
        amount=Decimal("750000.00"),
        value_date=date(2024, 1, 1),  # past date
        settlement_currency="AUD",
    ),
    # TRD-005: INSTRUMENT_NOT_FOUND — instrument not in reference data
    "TRD-005": TradeDetail(
        trade_id="TRD-005",
        counterparty_lei="9695005MSX1OYEMGDF46",
        instrument_id="UNKNOWN_CCY_PAIR",
        currency="USD",
        amount=Decimal("100000.00"),
        value_date=date(2026, 4, 8),
        settlement_currency="USD",
    ),
}

# ---------------------------------------------------------------------------
# SSI store (registered settlement instructions)
# ---------------------------------------------------------------------------

_SSIS: dict[tuple[str, str], SettlementInstruction] = {
    # TRD-001: intentionally NO entry for "213800QILIUD4ROSUO03" / "USD"
    # TRD-002: SSI exists but BIC is malformed (9 chars — invalid)
    ("5493001KJTIIGC8Y1R12", "EUR"): SettlementInstruction(
        lei="5493001KJTIIGC8Y1R12",
        currency="EUR",
        bic="GLSBUSS33",  # 9 chars — invalid BIC format (must be 8 or 11)
        account="DE89370400440532013000",
        iban="DE89370400440532013000",
    ),
    # TRD-004 / TRD-005: valid SSI (failure is elsewhere)
    ("9695005MSX1OYEMGDF46", "AUD"): SettlementInstruction(
        lei="9695005MSX1OYEMGDF46",
        currency="AUD",
        bic="PACFJPJT",
        account="AU12345678901234",
        iban=None,
    ),
    ("9695005MSX1OYEMGDF46", "USD"): SettlementInstruction(
        lei="9695005MSX1OYEMGDF46",
        currency="USD",
        bic="PACFJPJT",
        account="US12345678901234",
        iban=None,
    ),
}

# ---------------------------------------------------------------------------
# Reference data store (instruments)
# ---------------------------------------------------------------------------

_REFERENCE_DATA: dict[str, ReferenceData] = {
    "USDJPY": ReferenceData(
        instrument_id="USDJPY",
        description="US Dollar / Japanese Yen",
        asset_class="FX",
        is_active=True,
    ),
    "EURUSD": ReferenceData(
        instrument_id="EURUSD",
        description="Euro / US Dollar",
        asset_class="FX",
        is_active=True,
    ),
    "GBPUSD": ReferenceData(
        instrument_id="GBPUSD",
        description="British Pound / US Dollar",
        asset_class="FX",
        is_active=True,
    ),
    "AUDUSD": ReferenceData(
        instrument_id="AUDUSD",
        description="Australian Dollar / US Dollar",
        asset_class="FX",
        is_active=True,
    ),
    # "UNKNOWN_CCY_PAIR" → intentionally absent (TRD-005 scenario)
}

# ---------------------------------------------------------------------------
# External SSI source (Bloomberg/Omgeo equivalent — read-only lookup)
# Used when internal SSI is missing; found data triggers HITL before register
# ---------------------------------------------------------------------------

_EXTERNAL_SSIS: dict[tuple[str, str], SettlementInstruction] = {
    # TRD-001: external source HAS the SSI → will trigger HITL to register it
    ("213800QILIUD4ROSUO03", "USD"): SettlementInstruction(
        lei="213800QILIUD4ROSUO03",
        currency="USD",
        bic="ACMEGB2L",
        account="GB29NWBK60161331926819",
        iban="GB29NWBK60161331926819",
    ),
}

# ---------------------------------------------------------------------------
# Public query functions (used by tools)
# ---------------------------------------------------------------------------


def get_trade(trade_id: str) -> TradeDetail | None:
    return _TRADES.get(trade_id)


def get_ssi(lei: str, currency: str) -> SettlementInstruction | None:
    return _SSIS.get((lei, currency))


def get_reference(instrument_id: str) -> ReferenceData | None:
    return _REFERENCE_DATA.get(instrument_id)


def get_counterparty(lei: str) -> Counterparty | None:
    return _COUNTERPARTIES.get(lei)


def get_external_ssi(lei: str, currency: str) -> SettlementInstruction | None:
    return _EXTERNAL_SSIS.get((lei, currency))


def register_ssi(ssi: SettlementInstruction) -> None:
    """Write SSI to the internal store (simulates registration)."""
    _SSIS[(ssi.lei, ssi.currency)] = ssi
