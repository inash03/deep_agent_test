"""Application settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.infrastructure.db.app_setting_repository import AppSettingRepository
from src.infrastructure.db.session import get_db
from src.presentation.schemas import (
    AppSettingListResponse,
    AppSettingOut,
    AppSettingUpdateRequest,
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def _to_out(row) -> AppSettingOut:
    return AppSettingOut(key=row.key, value=row.value, description=row.description)


@router.get("", response_model=AppSettingListResponse)
def list_settings(db: Session = Depends(get_db)) -> AppSettingListResponse:
    rows = AppSettingRepository(db).list()
    return AppSettingListResponse(items=[_to_out(r) for r in rows])


@router.patch("/{key}", response_model=AppSettingOut)
def update_setting(
    key: str,
    body: AppSettingUpdateRequest,
    db: Session = Depends(get_db),
) -> AppSettingOut:
    repo = AppSettingRepository(db)
    if repo.get(key) is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    row = repo.set(key, body.value)
    db.commit()
    return _to_out(row)
