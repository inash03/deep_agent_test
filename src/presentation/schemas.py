"""Pydantic request / response schemas for the Presentation layer.

These are deliberately separate from domain entities:
- Request schemas validate external input at the API boundary.
- Response schemas control what is exposed to callers (no leaking internals).
"""

from __future__ import annotations

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
