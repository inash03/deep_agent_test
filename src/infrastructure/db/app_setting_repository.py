"""Repository for AppSetting data."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.infrastructure.db.models import AppSettingModel


class AppSettingRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, key: str) -> AppSettingModel | None:
        return self._db.query(AppSettingModel).filter(AppSettingModel.key == key).first()

    def list(self) -> list[AppSettingModel]:
        return self._db.query(AppSettingModel).order_by(AppSettingModel.key).all()

    def set(self, key: str, value: str) -> AppSettingModel:
        row = self.get(key)
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = AppSettingModel(
                key=key,
                value=value,
                updated_at=datetime.now(timezone.utc),
            )
            self._db.add(row)
        self._db.flush()
        return row
