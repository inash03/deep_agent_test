"""SSI (Settlement Standing Instructions) CRUD router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.session import get_db
from src.infrastructure.db.ssi_repository import SsiRepository
from src.presentation.schemas import SsiListResponse, SsiOut, SsiUpdateRequest

router = APIRouter(prefix="/api/v1/ssis", tags=["ssis"])


@router.get("", response_model=SsiListResponse)
def list_ssis(
    lei: str | None = None,
    is_external: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> SsiListResponse:
    items, total = SsiRepository(db).list(lei=lei, is_external=is_external, limit=limit, offset=offset)
    return SsiListResponse(
        items=[
            SsiOut(
                id=row.id, lei=row.lei, currency=row.currency,
                bic=row.bic, account=row.account, iban=row.iban,
                is_external=row.is_external, updated_at=row.updated_at,
            )
            for row in items
        ],
        total=total,
    )


@router.get("/{ssi_id}", response_model=SsiOut)
def get_ssi(ssi_id: uuid.UUID, db: Session = Depends(get_db)) -> SsiOut:
    from src.infrastructure.db.models import SettlementInstructionModel
    row = db.query(SettlementInstructionModel).filter(SettlementInstructionModel.id == ssi_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="SSI not found")
    return SsiOut(
        id=row.id, lei=row.lei, currency=row.currency,
        bic=row.bic, account=row.account, iban=row.iban,
        is_external=row.is_external, updated_at=row.updated_at,
    )


@router.patch("/{ssi_id}", response_model=SsiOut)
def update_ssi(ssi_id: uuid.UUID, body: SsiUpdateRequest, db: Session = Depends(get_db)) -> SsiOut:
    from src.infrastructure.db.models import SettlementInstructionModel
    row = db.query(SettlementInstructionModel).filter(SettlementInstructionModel.id == ssi_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="SSI not found")
    if body.bic is not None:
        row.bic = body.bic
    if body.account is not None:
        row.account = body.account
    if body.iban is not None:
        row.iban = body.iban
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return SsiOut(
        id=row.id, lei=row.lei, currency=row.currency,
        bic=row.bic, account=row.account, iban=row.iban,
        is_external=row.is_external, updated_at=row.updated_at,
    )
