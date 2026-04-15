"""Repository for Counterparty data."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.entities import Counterparty
from src.infrastructure.db.models import CounterpartyModel


class CounterpartyRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self,
        lei: str | None = None,
        name: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[CounterpartyModel], int]:
        q = self._db.query(CounterpartyModel)
        if lei:
            q = q.filter(CounterpartyModel.lei.ilike(f"%{lei}%"))
        if name:
            q = q.filter(CounterpartyModel.name.ilike(f"%{name}%"))
        total = q.count()
        items = q.order_by(CounterpartyModel.name).offset(offset).limit(limit).all()
        return items, total

    def get_by_lei(self, lei: str) -> CounterpartyModel | None:
        return self._db.query(CounterpartyModel).filter(CounterpartyModel.lei == lei).first()

    def update(self, lei: str, name: str | None, bic: str | None, is_active: bool | None) -> CounterpartyModel | None:
        row = self.get_by_lei(lei)
        if row is None:
            return None
        if name is not None:
            row.name = name
        if bic is not None:
            row.bic = bic
        if is_active is not None:
            row.is_active = is_active
        row.updated_at = datetime.now(timezone.utc)
        self._db.commit()
        self._db.refresh(row)
        return row

    @staticmethod
    def to_domain(row: CounterpartyModel) -> Counterparty:
        return Counterparty(lei=row.lei, name=row.name, bic=row.bic, is_active=row.is_active)
