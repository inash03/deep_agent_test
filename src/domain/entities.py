"""Domain entities for the STP Exception Triage Agent.

Pure business logic — no framework dependencies.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class RootCause(str, Enum):
    MISSING_SSI = "MISSING_SSI"
    BIC_FORMAT_ERROR = "BIC_FORMAT_ERROR"
    INVALID_VALUE_DATE = "INVALID_VALUE_DATE"
    INSTRUMENT_NOT_FOUND = "INSTRUMENT_NOT_FOUND"
    COUNTERPARTY_NOT_FOUND = "COUNTERPARTY_NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class TriageStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------


class STPFailure(BaseModel):
    """Input to the triage use case — a single STP failure notification."""

    trade_id: str = Field(..., min_length=1)
    error_message: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Intermediate data (populated by tools during the ReAct loop)
# ---------------------------------------------------------------------------


class TradeDetail(BaseModel):
    """Trade information retrieved from the trade system."""

    trade_id: str
    counterparty_lei: str
    instrument_id: str
    currency: str
    amount: Decimal
    value_date: date
    settlement_currency: str


class SettlementInstruction(BaseModel):
    """SSI (Settlement Standing Instruction) for a counterparty/currency pair."""

    lei: str
    currency: str
    bic: str
    account: str
    iban: str | None = None


class ReferenceData(BaseModel):
    """Instrument reference data."""

    instrument_id: str
    description: str
    asset_class: str
    is_active: bool


class Counterparty(BaseModel):
    """Counterparty master data."""

    lei: str
    name: str
    bic: str
    is_active: bool


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------


class Step(BaseModel):
    """A single recorded step in the agent's execution (tool call or HITL event)."""

    step_type: Literal["tool_call", "hitl_prompt", "hitl_response"]
    name: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    approved: bool | None = None  # only set for hitl_response steps


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


class TriageResult(BaseModel):
    """Final output of the triage use case."""

    trade_id: str
    status: TriageStatus

    # Populated when status == PENDING_APPROVAL
    run_id: str | None = None
    pending_action_description: str | None = None

    # Populated when status == COMPLETED
    diagnosis: str | None = None
    root_cause: RootCause | None = None
    recommended_action: str | None = None
    action_taken: bool = False

    # Always populated
    steps: list[Step] = Field(default_factory=list)
