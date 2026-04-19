"""STP Exception CRUD + start-triage endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.domain.entities import STPFailure, StpExceptionStatus, TriageStatus
from src.infrastructure.db.repository import TriageResultRepository
from src.infrastructure.db.session import get_db
from src.infrastructure.db.stp_exception_repository import StpExceptionRepository
from src.infrastructure.db.trade_repository import TradeRepository
from src.presentation.dependencies import verify_api_key
from src.presentation.router import get_use_case
from src.presentation.schemas import (
    StpExceptionCreateRequest,
    StpExceptionListResponse,
    StpExceptionOut,
    StpExceptionStatusUpdateRequest,
    TriageResponse,
)

router = APIRouter(prefix="/api/v1/stp-exceptions", tags=["stp-exceptions"])


def _to_out(row) -> StpExceptionOut:
    return StpExceptionOut(
        id=row.id,
        trade_id=row.trade_id,
        error_message=row.error_message,
        status=row.status,
        triage_run_id=row.triage_run_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=StpExceptionListResponse)
def list_stp_exceptions(
    status: str | None = Query(None, description="ステータスフィルタ (e.g. OPEN)"),
    trade_id: str | None = Query(None, description="Trade ID 部分一致フィルタ"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> StpExceptionListResponse:
    repo = StpExceptionRepository(db)
    items, total = repo.list(status=status, trade_id=trade_id, limit=limit, offset=offset)
    return StpExceptionListResponse(items=[_to_out(r) for r in items], total=total)


@router.get("/{id}", response_model=StpExceptionOut)
def get_stp_exception(id: uuid.UUID, db: Session = Depends(get_db)) -> StpExceptionOut:
    row = StpExceptionRepository(db).get_by_id(id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"STP Exception '{id}' not found")
    return _to_out(row)


@router.post("", response_model=StpExceptionOut, status_code=201)
def create_stp_exception(
    body: StpExceptionCreateRequest,
    db: Session = Depends(get_db),
) -> StpExceptionOut:
    trade = TradeRepository(db).get_by_trade_id(body.trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade '{body.trade_id}' not found")
    if trade.stp_status != "NEW":
        raise HTTPException(
            status_code=422,
            detail=f"Trade '{body.trade_id}' has stp_status='{trade.stp_status}'. Only NEW trades can have exceptions created manually.",
        )
    row = StpExceptionRepository(db).create(
        trade_id=body.trade_id, error_message=body.error_message
    )
    return _to_out(row)


@router.patch("/{id}", response_model=StpExceptionOut)
def update_stp_exception_status(
    id: uuid.UUID,
    body: StpExceptionStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> StpExceptionOut:
    row = StpExceptionRepository(db).update_status(id, body.status)
    if row is None:
        raise HTTPException(status_code=404, detail=f"STP Exception '{id}' not found")
    return _to_out(row)


@router.post("/{id}/start-triage", response_model=TriageResponse)
def start_triage_for_exception(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    use_case=Depends(get_use_case),
    _: None = Depends(verify_api_key),
) -> TriageResponse:
    exc_repo = StpExceptionRepository(db)
    exc = exc_repo.get_by_id(id)
    if exc is None:
        raise HTTPException(status_code=404, detail=f"STP Exception '{id}' not found")

    failure = STPFailure(trade_id=exc.trade_id, error_message=exc.error_message)
    result = use_case.start(failure)

    # Save triage result to DB
    TriageResultRepository(db).save(result)

    # Update exception: status → IN_PROGRESS or RESOLVED; link triage run if available
    new_status = (
        StpExceptionStatus.IN_PROGRESS.value
        if result.status == TriageStatus.PENDING_APPROVAL
        else StpExceptionStatus.RESOLVED.value
    )
    exc_repo.update_status(id, new_status)

    if result.run_id:
        try:
            exc_repo.link_triage_run(id, uuid.UUID(result.run_id))
        except (ValueError, AttributeError):
            pass  # run_id format mismatch — skip linking

    return TriageResponse.from_domain(result)
