"""Trade list, creation and check endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.db.models import TradeModel
from src.infrastructure.db.session import get_db
from src.infrastructure.db.trade_repository import TradeRepository
from src.infrastructure.rule_engine import maybe_run_bo_check, maybe_run_fo_check, run_bo_check, run_fo_check
from src.presentation.schemas import (
    CheckResultOut,
    CheckResultsResponse,
    TradeCreateRequest,
    TradeListResponse,
    TradeOut,
)

router = APIRouter(prefix="/api/v1/trades", tags=["trades"])
_logger = logging.getLogger("stp_triage.trades")


def _to_out(row) -> TradeOut:
    return TradeOut(
        trade_id=row.trade_id,
        version=row.version,
        workflow_status=row.workflow_status,
        is_current=row.is_current,
        counterparty_lei=row.counterparty_lei,
        instrument_id=row.instrument_id,
        currency=row.currency,
        amount=str(row.amount),
        value_date=row.value_date,
        trade_date=row.trade_date,
        settlement_currency=row.settlement_currency,
        stp_status=row.stp_status,
        fo_check_results=row.fo_check_results,
        bo_check_results=row.bo_check_results,
    )


@router.get("", response_model=TradeListResponse)
def list_trades(
    trade_id: str | None = Query(None, description="部分一致フィルタ"),
    stp_status: str | None = Query(None, description="完全一致フィルタ (e.g. STP_FAILED)"),
    workflow_status: str | None = Query(None, description="完全一致フィルタ (e.g. FoAgentToCheck)"),
    trade_date: date | None = Query(None, description="取引日フィルタ (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> TradeListResponse:
    repo = TradeRepository(db)
    items, total = repo.list(
        trade_id=trade_id, stp_status=stp_status, workflow_status=workflow_status,
        trade_date=trade_date, limit=limit, offset=offset,
    )
    return TradeListResponse(items=[_to_out(r) for r in items], total=total)


@router.post("", response_model=TradeOut, status_code=201)
def create_trade(body: TradeCreateRequest, db: Session = Depends(get_db)) -> TradeOut:
    """Create a new trade and trigger FoCheck workflow.

    ``trade_id`` is assigned by the server at insert time (TRD-001 style sequence).
    """
    repo = TradeRepository(db)
    assigned_id: str | None = None
    for _ in range(32):
        trade_id = repo.allocate_next_trade_id()
        row = TradeModel(
            id=uuid.uuid4(),
            trade_id=trade_id,
            version=1,
            workflow_status="Initial",
            is_current=True,
            counterparty_lei=body.counterparty_lei,
            instrument_id=body.instrument_id,
            currency=body.currency,
            amount=body.amount,
            value_date=body.value_date,
            trade_date=body.trade_date,
            settlement_currency=body.currency,
            stp_status="NEW",
            sendback_count=0,
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        assigned_id = trade_id
        break

    if assigned_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not allocate a unique trade id; please retry.",
        )

    try:
        maybe_run_fo_check(assigned_id, db)
    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "fo_check auto-trigger failed after trade creation",
            extra={"trade_id": assigned_id, "error": str(exc)},
        )

    row = repo.get_by_trade_id(assigned_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trade was created but could not be reloaded.",
        )
    return _to_out(row)


@router.get("/{trade_id}", response_model=TradeOut)
def get_trade(trade_id: str, db: Session = Depends(get_db)) -> TradeOut:
    row = TradeRepository(db).get_by_trade_id(trade_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' not found")
    return _to_out(row)


@router.post("/{trade_id}/fo-check", response_model=CheckResultsResponse)
def fo_check(trade_id: str, db: Session = Depends(get_db)) -> CheckResultsResponse:
    """Run FoCheck rules and advance workflow_status to FoValidated or FoAgentToCheck."""
    try:
        results, new_status = run_fo_check(trade_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if new_status == "FoValidated":
        try:
            maybe_run_bo_check(trade_id, db)
        except Exception as exc:  # noqa: BLE001
            _logger.warning(
                "bo_check auto-trigger failed after fo_check",
                extra={"trade_id": trade_id, "error": str(exc)},
            )

    return CheckResultsResponse(
        trade_id=trade_id,
        workflow_status=new_status,
        results=[
            CheckResultOut(
                rule_name=r.rule_name, passed=r.passed,
                severity=r.severity, message=r.message,
            )
            for r in results
        ],
    )


@router.post("/{trade_id}/bo-check", response_model=CheckResultsResponse)
def bo_check(trade_id: str, db: Session = Depends(get_db)) -> CheckResultsResponse:
    """Run BoCheck rules and advance workflow_status to BoValidated or BoAgentToCheck."""
    try:
        results, new_status = run_bo_check(trade_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return CheckResultsResponse(
        trade_id=trade_id,
        workflow_status=new_status,
        results=[
            CheckResultOut(
                rule_name=r.rule_name, passed=r.passed,
                severity=r.severity, message=r.message,
            )
            for r in results
        ],
    )
