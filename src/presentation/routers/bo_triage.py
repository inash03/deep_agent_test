"""FastAPI router for BO STP triage (trade-level endpoints).

Endpoints:
  POST /api/v1/trades/{trade_id}/bo-triage           — start a new BO triage run
  POST /api/v1/trades/{trade_id}/bo-triage/{run_id}/resume — resume PENDING_APPROVAL
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.infrastructure.bo_triage_use_case import BoTriageUseCase
from src.infrastructure.db.llm_cost_log_repository import LlmCostLogRepository
from src.infrastructure.db.repository import TriageResultRepository
from src.infrastructure.db.session import get_db
from src.presentation.dependencies import limiter, verify_api_key
from src.presentation.schemas import ResumeRequest, TriageRequest, TriageResponse

_logger = logging.getLogger("stp_triage.bo_triage_router")

router = APIRouter(prefix="/api/v1/trades", tags=["bo-triage"])

# ---------------------------------------------------------------------------
# Singleton — MemorySaver must persist across requests
# ---------------------------------------------------------------------------

_bo_use_case: BoTriageUseCase | None = None


def get_bo_use_case() -> BoTriageUseCase:
    global _bo_use_case
    if _bo_use_case is None:
        _bo_use_case = BoTriageUseCase()
    return _bo_use_case


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{trade_id}/bo-triage",
    response_model=TriageResponse,
    summary="Start BO triage for a trade",
    description=(
        "Launches the BoAgent ReAct loop to investigate BoCheck failures for the given trade. "
        "Returns COMPLETED with a diagnosis, or PENDING_APPROVAL with a run_id "
        "when the agent needs operator approval (e.g. register SSI, reactivate counterparty)."
    ),
)
@limiter.limit("5/minute")
def start_bo_triage(
    request: Request,
    trade_id: str,
    body: TriageRequest,
    use_case: BoTriageUseCase = Depends(get_bo_use_case),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> TriageResponse:
    result = use_case.start(trade_id=trade_id, error_context=body.error_message)
    _save_cost_logs(db, result, agent_type="bo")
    _save_triage_result(db, result)
    return TriageResponse.from_domain(result)


@router.post(
    "/{trade_id}/bo-triage/{run_id}/resume",
    response_model=TriageResponse,
    summary="Resume a PENDING_APPROVAL BO triage run",
    description=(
        "Resumes a BO triage run waiting for operator approval. "
        "Set approved=true to allow the pending action, or approved=false to skip it."
    ),
)
@limiter.limit("5/minute")
def resume_bo_triage(
    request: Request,
    trade_id: str,
    run_id: str,
    body: ResumeRequest,
    use_case: BoTriageUseCase = Depends(get_bo_use_case),
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> TriageResponse:
    try:
        result = use_case.resume(run_id, approved=body.approved)
    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail=f"BO triage run '{run_id}' not found or already completed.",
        )
    _save_cost_logs(db, result, agent_type="bo")
    _save_triage_result(db, result)
    return TriageResponse.from_domain(result)


def _save_triage_result(db: Session, result) -> None:
    try:
        TriageResultRepository(db).save(result)
    except Exception as exc:
        _logger.warning("Failed to save triage result to history: %s", exc)


def _save_cost_logs(db: Session, result, agent_type: str) -> None:
    if not result.cost_log:
        return
    try:
        repo = LlmCostLogRepository(db)
        repo.save_batch(result.cost_log, result.run_id or "", result.trade_id, agent_type)
        db.commit()
    except Exception as exc:
        _logger.warning("Failed to save cost logs: %s", exc)
        db.rollback()
