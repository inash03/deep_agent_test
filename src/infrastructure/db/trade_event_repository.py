"""Repository for TradeEvent data."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.entities import TradeEvent, EventType, EventWorkflowStatus
from src.infrastructure.db.models import TradeEventModel

_TERMINAL_STATUSES = {"Done", "Cancelled"}


class TradeEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_trade(self, trade_id: str) -> list[TradeEventModel]:
        return (
            self._db.query(TradeEventModel)
            .filter(TradeEventModel.trade_id == trade_id)
            .order_by(TradeEventModel.created_at.desc())
            .all()
        )

    def get_pending(self, trade_id: str) -> TradeEventModel | None:
        """Return the in-flight event (not yet Done/Cancelled) for a trade."""
        return (
            self._db.query(TradeEventModel)
            .filter(
                TradeEventModel.trade_id == trade_id,
                TradeEventModel.workflow_status.notin_(_TERMINAL_STATUSES),
            )
            .first()
        )

    def create(
        self,
        trade_id: str,
        from_version: int,
        to_version: int,
        event_type: str,
        requested_by: str,
        reason: str | None = None,
        amended_fields: dict | None = None,
    ) -> TradeEventModel:
        row = TradeEventModel(
            id=uuid.uuid4(),
            trade_id=trade_id,
            from_version=from_version,
            to_version=to_version,
            event_type=event_type,
            workflow_status="FoUserToValidate",
            requested_by=requested_by,
            reason=reason,
            amended_fields=amended_fields,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(row)
        self._db.flush()
        return row

    def update_status(self, event_id: uuid.UUID, status: str) -> TradeEventModel | None:
        row = self._db.query(TradeEventModel).filter(TradeEventModel.id == event_id).first()
        if row:
            row.workflow_status = status
            row.updated_at = datetime.now(timezone.utc)
            self._db.flush()
        return row

    @staticmethod
    def to_domain(row: TradeEventModel) -> TradeEvent:
        return TradeEvent(
            id=row.id,
            trade_id=row.trade_id,
            from_version=row.from_version,
            to_version=row.to_version,
            event_type=EventType(row.event_type),
            workflow_status=EventWorkflowStatus(row.workflow_status),
            requested_by=row.requested_by,
            reason=row.reason,
            amended_fields=row.amended_fields,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
