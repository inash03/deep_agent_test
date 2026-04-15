"""Counterparty list and edit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.counterparty_repository import CounterpartyRepository
from src.infrastructure.db.session import get_db
from src.presentation.schemas import (
    CounterpartyListResponse,
    CounterpartyOut,
    CounterpartyUpdateRequest,
)

router = APIRouter(prefix="/api/v1/counterparties", tags=["counterparties"])


def _to_out(row) -> CounterpartyOut:
    return CounterpartyOut(lei=row.lei, name=row.name, bic=row.bic, is_active=row.is_active)


@router.get("", response_model=CounterpartyListResponse)
def list_counterparties(
    lei: str | None = Query(None, description="LEI 部分一致フィルタ"),
    name: str | None = Query(None, description="名前部分一致フィルタ"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> CounterpartyListResponse:
    repo = CounterpartyRepository(db)
    items, total = repo.list(lei=lei, name=name, limit=limit, offset=offset)
    return CounterpartyListResponse(items=[_to_out(r) for r in items], total=total)


@router.get("/{lei}", response_model=CounterpartyOut)
def get_counterparty(lei: str, db: Session = Depends(get_db)) -> CounterpartyOut:
    row = CounterpartyRepository(db).get_by_lei(lei)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Counterparty '{lei}' not found")
    return _to_out(row)


@router.patch("/{lei}", response_model=CounterpartyOut)
def update_counterparty(
    lei: str,
    body: CounterpartyUpdateRequest,
    db: Session = Depends(get_db),
) -> CounterpartyOut:
    row = CounterpartyRepository(db).update(
        lei, name=body.name, bic=body.bic, is_active=body.is_active
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Counterparty '{lei}' not found")
    return _to_out(row)
