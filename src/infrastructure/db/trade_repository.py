"""Repository for Trade data."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from src.domain.entities import TradeDetail, TradeStatus
from src.infrastructure.db.models import TradeModel


class TradeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self,
        trade_id: str | None = None,
        stp_status: str | None = None,
        trade_date: date | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TradeModel], int]:
        q = self._db.query(TradeModel)
        if trade_id:
            q = q.filter(TradeModel.trade_id.ilike(f"%{trade_id}%"))
        if stp_status:
            q = q.filter(TradeModel.stp_status == stp_status)
        if trade_date:
            q = q.filter(TradeModel.trade_date == trade_date)
        total = q.count()
        items = q.order_by(TradeModel.trade_date.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_by_trade_id(self, trade_id: str) -> TradeModel | None:
        return self._db.query(TradeModel).filter(TradeModel.trade_id == trade_id).first()

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
