"""Reference Data (instruments) read-only router."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.infrastructure.db.reference_data_repository import ReferenceDataRepository
from src.infrastructure.db.session import get_db
from src.presentation.schemas import ReferenceDataListResponse, ReferenceDataOut

router = APIRouter(prefix="/api/v1/reference-data", tags=["reference-data"])


@router.get("", response_model=ReferenceDataListResponse)
def list_reference_data(db: Session = Depends(get_db)) -> ReferenceDataListResponse:
    rows = ReferenceDataRepository(db).list()
    return ReferenceDataListResponse(
        items=[
            ReferenceDataOut(
                instrument_id=r.instrument_id,
                description=r.description,
                asset_class=r.asset_class,
                is_active=r.is_active,
            )
            for r in rows
        ],
        total=len(rows),
    )
