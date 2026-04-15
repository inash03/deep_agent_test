"""Repository for STP Exception data."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.entities import StpException, StpExceptionStatus
from src.infrastructure.db.models import StpExceptionModel


class StpExceptionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self,
        status: str | None = None,
        trade_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[StpExceptionModel], int]:
        q = self._db.query(StpExceptionModel)
        if status:
            q = q.filter(StpExceptionModel.status == status)
        if trade_id:
            q = q.filter(StpExceptionModel.trade_id.ilike(f"%{trade_id}%"))
        total = q.count()
        items = q.order_by(StpExceptionModel.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_id(self, id: uuid.UUID) -> StpExceptionModel | None:
        return self._db.query(StpExceptionModel).filter(StpExceptionModel.id == id).first()

    def create(self, trade_id: str, error_message: str) -> StpExceptionModel:
        now = datetime.now(timezone.utc)
        row = StpExceptionModel(
            id=uuid.uuid4(),
            trade_id=trade_id,
            error_message=error_message,
            status=StpExceptionStatus.OPEN.value,
            triage_run_id=None,
            created_at=now,
            updated_at=now,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update_status(self, id: uuid.UUID, status: str) -> StpExceptionModel | None:
        row = self.get_by_id(id)
        if row is None:
            return None
        row.status = status
        row.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(row)
        return row

    def link_triage_run(self, id: uuid.UUID, triage_run_id: uuid.UUID) -> None:
        row = self.get_by_id(id)
        if row is None:
            return
        row.triage_run_id = triage_run_id
        row.updated_at = datetime.now(timezone.utc)
        self._db.commit()

    @staticmethod
    def to_domain(row: StpExceptionModel) -> StpException:
        return StpException(
            id=row.id,
            trade_id=row.trade_id,
            error_message=row.error_message,
            status=StpExceptionStatus(row.status),
            triage_run_id=row.triage_run_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
