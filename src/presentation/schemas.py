"""Pydantic request / response schemas for the Presentation layer.

These are deliberately separate from domain entities:
- Request schemas validate external input at the API boundary.
- Response schemas control what is exposed to callers (no leaking internals).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.entities import TriageResult


class TriageRequest(BaseModel):
    trade_id: str = Field(..., min_length=1, examples=["TRD-001"])
    error_message: str = Field(
        ...,
        min_length=1,
        examples=["SETT FAIL - SSI not found for counterparty LEI 213800QILIUD4ROSUO03"],
    )


class ResumeRequest(BaseModel):
    approved: bool = Field(
        ...,
        description="True to approve the pending action; False to reject it.",
    )


class StepOut(BaseModel):
    step_type: str
    name: str
    input: dict
    output: dict | None = None


class TriageResponse(BaseModel):
    trade_id: str
    status: str  # "COMPLETED" | "PENDING_APPROVAL"

    # Set when status == PENDING_APPROVAL
    run_id: str | None = None
    pending_action_type: str | None = None
    pending_action_description: str | None = None

    # Set when status == COMPLETED
    diagnosis: str | None = None
    root_cause: str | None = None
    recommended_action: str | None = None
    action_taken: bool = False

    steps: list[StepOut] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: TriageResult) -> "TriageResponse":
        return cls(
            trade_id=result.trade_id,
            status=result.status.value,
            run_id=result.run_id,
            pending_action_type=result.pending_action_type,
            pending_action_description=result.pending_action_description,
            diagnosis=result.diagnosis,
            root_cause=result.root_cause.value if result.root_cause else None,
            recommended_action=result.recommended_action,
            action_taken=result.action_taken,
            steps=[
                StepOut(
                    step_type=s.step_type,
                    name=s.name,
                    input=s.input,
                    output=s.output,
                )
                for s in result.steps
            ],
        )


class TriageHistoryResponse(BaseModel):
    """GET /api/v1/triage/history のレスポンス。"""

    items: list[TriageResponse]
    total: int


# ---------------------------------------------------------------------------
# Trade schemas
# ---------------------------------------------------------------------------


class TradeOut(BaseModel):
    trade_id: str
    version: int
    workflow_status: str
    is_current: bool
    counterparty_lei: str
    instrument_id: str
    currency: str
    amount: str  # string to preserve decimal precision
    value_date: date
    trade_date: date
    settlement_currency: str
    stp_status: str
    fo_check_results: list[dict] | None = None
    bo_check_results: list[dict] | None = None


class TradeListResponse(BaseModel):
    items: list[TradeOut]
    total: int


class TradeCreateRequest(BaseModel):
    trade_id: str = Field(..., min_length=1, examples=["TRD-020"])
    trade_date: date
    value_date: date
    counterparty_lei: str = Field(..., min_length=1)
    instrument_id: str = Field(..., min_length=1)
    currency: str = Field(..., min_length=3, max_length=10)
    amount: Decimal = Field(..., gt=Decimal("0"))


# ---------------------------------------------------------------------------
# Counterparty schemas
# ---------------------------------------------------------------------------


class CounterpartyOut(BaseModel):
    lei: str
    name: str
    bic: str
    is_active: bool


class CounterpartyListResponse(BaseModel):
    items: list[CounterpartyOut]
    total: int


class CounterpartyUpdateRequest(BaseModel):
    name: str | None = None
    bic: str | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# STP Exception schemas
# ---------------------------------------------------------------------------


class StpExceptionOut(BaseModel):
    id: uuid.UUID
    trade_id: str
    error_message: str
    status: str
    triage_run_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class StpExceptionListResponse(BaseModel):
    items: list[StpExceptionOut]
    total: int


class StpExceptionCreateRequest(BaseModel):
    trade_id: str = Field(..., min_length=1, examples=["TRD-006"])
    error_message: str = Field(..., min_length=1, examples=["Manual STP failure for demo"])


class StpExceptionStatusUpdateRequest(BaseModel):
    status: str = Field(..., examples=["IN_PROGRESS"])


# ---------------------------------------------------------------------------
# SSI schemas
# ---------------------------------------------------------------------------


class SsiOut(BaseModel):
    id: uuid.UUID
    lei: str
    currency: str
    bic: str
    account: str
    iban: str | None = None
    is_external: bool
    updated_at: datetime


class SsiListResponse(BaseModel):
    items: list[SsiOut]
    total: int


class SsiUpdateRequest(BaseModel):
    bic: str | None = None
    account: str | None = None
    iban: str | None = None


# ---------------------------------------------------------------------------
# Reference Data schemas
# ---------------------------------------------------------------------------


class ReferenceDataOut(BaseModel):
    instrument_id: str
    description: str
    asset_class: str
    is_active: bool


class ReferenceDataListResponse(BaseModel):
    items: list[ReferenceDataOut]
    total: int


# ---------------------------------------------------------------------------
# Check result schemas (FoCheck / BoCheck)
# ---------------------------------------------------------------------------


class CheckResultOut(BaseModel):
    rule_name: str
    passed: bool
    severity: str
    message: str


class CheckResultsResponse(BaseModel):
    trade_id: str
    workflow_status: str
    results: list[CheckResultOut]


# ---------------------------------------------------------------------------
# App settings schemas
# ---------------------------------------------------------------------------


class AppSettingOut(BaseModel):
    key: str
    value: str
    description: str | None = None


class AppSettingListResponse(BaseModel):
    items: list[AppSettingOut]


class AppSettingUpdateRequest(BaseModel):
    value: str = Field(..., examples=["auto"])


# ---------------------------------------------------------------------------
# Trade Event schemas (Phase 26-E)
# ---------------------------------------------------------------------------


class TradeVersionOut(BaseModel):
    """A specific version of a trade (used in event responses)."""
    trade_id: str
    version: int
    workflow_status: str
    is_current: bool
    counterparty_lei: str
    instrument_id: str
    currency: str
    amount: str
    value_date: date
    trade_date: date
    settlement_currency: str


class TradeEventOut(BaseModel):
    id: uuid.UUID
    trade_id: str
    from_version: int
    to_version: int
    event_type: str        # AMEND | CANCEL
    workflow_status: str   # FoUserToValidate | FoValidated | Done | Cancelled
    requested_by: str
    reason: str | None = None
    amended_fields: dict | None = None
    created_at: datetime
    updated_at: datetime


class TradeEventListResponse(BaseModel):
    items: list[TradeEventOut]
    total: int


class TradeEventCreateRequest(BaseModel):
    event_type: str = Field(..., examples=["AMEND"], description="AMEND or CANCEL")
    reason: str = Field(..., min_length=1)
    requested_by: str = Field(..., min_length=1, examples=["fo_user_01"])
    amended_fields: dict | None = Field(
        default=None,
        description="Required for AMEND. Keys: value_date, trade_date, amount, currency, settlement_currency, instrument_id.",
        examples=[{"value_date": "2026-05-01"}],
    )


class EventApproveRequest(BaseModel):
    approved: bool
    comment: str | None = None
