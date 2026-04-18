"""FastAPI router for FO STP triage (trade-level endpoints).

Endpoints:
  POST /api/v1/trades/{trade_id}/fo-triage           — start a new FO triage run
  POST /api/v1/trades/{trade_id}/fo-triage/{run_id}/resume — resume PENDING_APPROVAL
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.infrastructure.fo_triage_use_case import FoTriageUseCase
from src.presentation.dependencies import verify_api_key
from src.presentation.schemas import ResumeRequest, TriageRequest, TriageResponse

router = APIRouter(prefix="/api/v1/trades", tags=["fo-triage"])

# ---------------------------------------------------------------------------
# Singleton — MemorySaver must persist across requests
# ---------------------------------------------------------------------------

_fo_use_case: FoTriageUseCase | None = None


def get_fo_use_case() -> FoTriageUseCase:
    global _fo_use_case
    if _fo_use_case is None:
        _fo_use_case = FoTriageUseCase()
    return _fo_use_case


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{trade_id}/fo-triage",
    response_model=TriageResponse,
    summary="Start FO triage for a trade",
    description=(
        "Launches the FoAgent ReAct loop to investigate FoCheck failures for the given trade. "
        "Returns COMPLETED with a diagnosis, or PENDING_APPROVAL with a run_id "
        "when the agent needs operator approval (e.g. amend trade data, cancel trade)."
    ),
)
def start_fo_triage(
    trade_id: str,
    body: TriageRequest,
    use_case: FoTriageUseCase = Depends(get_fo_use_case),
    _: None = Depends(verify_api_key),
) -> TriageResponse:
    result = use_case.start(trade_id=trade_id, error_context=body.error_message)
    return TriageResponse.from_domain(result)


@router.post(
    "/{trade_id}/fo-triage/{run_id}/resume",
    response_model=TriageResponse,
    summary="Resume a PENDING_APPROVAL FO triage run",
    description=(
        "Resumes a FO triage run waiting for operator approval. "
        "Set approved=true to allow the pending action, or approved=false to skip it."
    ),
)
def resume_fo_triage(
    trade_id: str,
    run_id: str,
    body: ResumeRequest,
    use_case: FoTriageUseCase = Depends(get_fo_use_case),
    _: None = Depends(verify_api_key),
) -> TriageResponse:
    try:
        result = use_case.resume(run_id, approved=body.approved)
    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail=f"FO triage run '{run_id}' not found or already completed.",
        )
    return TriageResponse.from_domain(result)
