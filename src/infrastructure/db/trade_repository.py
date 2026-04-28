"""Repository for Trade data."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.domain.entities import TradeDetail
from src.infrastructure.db.models import TradeModel

_TRD_NUMERIC_ID = re.compile(r"^TRD-(\d+)$", re.IGNORECASE)


class TradeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def allocate_next_trade_id(self) -> str:
        """Next TRD-001 style id from all current trade rows (matches seed data)."""
        rows = (
            self._db.query(TradeModel.trade_id)
            .filter(TradeModel.is_current.is_(True))
            .all()
        )
        max_n = 0
        for (tid,) in rows:
            m = _TRD_NUMERIC_ID.match(tid)
            if m:
                max_n = max(max_n, int(m.group(1)))
        return f"TRD-{max_n + 1:03d}"

    def list(
        self,
        trade_id: str | None = None,
        workflow_status: str | None = None,
        trade_date: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TradeModel], int]:
        """Return only is_current=True rows (active trade versions)."""
        q = self._db.query(TradeModel).filter(TradeModel.is_current.is_(True))
        if trade_id:
            q = q.filter(TradeModel.trade_id.ilike(f"%{trade_id}%"))
        if workflow_status:
            q = q.filter(TradeModel.workflow_status == workflow_status)
        if trade_date:
            q = q.filter(TradeModel.trade_date == trade_date)
        total = q.count()
        items = q.order_by(TradeModel.trade_date.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_trade_id(self, trade_id: str) -> TradeModel | None:
        """Return the current (is_current=True) version of the trade."""
        return (
            self._db.query(TradeModel)
            .filter(TradeModel.trade_id == trade_id, TradeModel.is_current.is_(True))
            .first()
        )

    def get_current(self, trade_id: str) -> TradeModel | None:
        """Alias for get_by_trade_id — returns the active version."""
        return self.get_by_trade_id(trade_id)

    def list_versions(self, trade_id: str) -> list[TradeModel]:
        """Return all versions of a trade ordered by version ascending."""
        return (
            self._db.query(TradeModel)
            .filter(TradeModel.trade_id == trade_id)
            .order_by(TradeModel.version.asc())
            .all()
        )

    def create_next_version(
        self,
        trade_id: str,
        event_type: str,
        amended_fields: dict[str, Any] | None = None,
    ) -> TradeModel:
        """Create a new EventPending version from the current active version.

        The new row copies all fields from the current version, increments
        version by 1, sets workflow_status=EventPending, and is_current=False
        (it becomes current only after the event is approved).
        """
        current = self.get_current(trade_id)
        if current is None:
            raise ValueError(f"Trade '{trade_id}' not found")

        new_version = current.version + 1
        fields = amended_fields or {}
        new_row = TradeModel(
            trade_id=trade_id,
            version=new_version,
            workflow_status="EventPending",
            is_current=False,
            counterparty_lei=fields.get("counterparty_lei", current.counterparty_lei),
            instrument_id=fields.get("instrument_id", current.instrument_id),
            currency=fields.get("currency", current.currency),
            amount=fields.get("amount", current.amount),
            value_date=fields.get("value_date", current.value_date),
            trade_date=fields.get("trade_date", current.trade_date),
            settlement_currency=fields.get("settlement_currency", current.settlement_currency),
            sendback_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(new_row)
        self._db.flush()
        return new_row

    def activate_version(self, trade_id: str, version: int) -> TradeModel | None:
        """Flip is_current: deactivate all other versions, activate this one."""
        rows = (
            self._db.query(TradeModel)
            .filter(TradeModel.trade_id == trade_id)
            .all()
        )
        target: TradeModel | None = None
        for row in rows:
            if row.version == version:
                row.is_current = True
                row.updated_at = datetime.now(timezone.utc)
                target = row
            else:
                row.is_current = False
                row.updated_at = datetime.now(timezone.utc)
        self._db.flush()
        return target

    def update_workflow_status(
        self,
        trade_id: str,
        status: str,
        **kwargs: Any,
    ) -> TradeModel | None:
        """Update workflow_status on the current version, plus any extra fields."""
        row = self.get_current(trade_id)
        if row is None:
            return None
        row.workflow_status = status
        row.updated_at = datetime.now(timezone.utc)
        for field, value in kwargs.items():
            setattr(row, field, value)
        self._db.flush()
        return row

    @staticmethod
    def to_domain(row: TradeModel) -> TradeDetail:
        return TradeDetail(
            trade_id=row.trade_id,
            counterparty_lei=row.counterparty_lei,
            instrument_id=row.instrument_id,
            currency=row.currency,
            amount=row.amount,
            value_date=row.value_date,
            settlement_currency=row.settlement_currency,
        )
