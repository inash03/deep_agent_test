"""Repository for Settlement Instructions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.entities import SettlementInstruction
from src.infrastructure.db.models import SettlementInstructionModel


class SsiRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(
        self,
        lei: str | None = None,
        is_external: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SettlementInstructionModel], int]:
        q = self._db.query(SettlementInstructionModel)
        if lei:
            q = q.filter(SettlementInstructionModel.lei.ilike(f"%{lei}%"))
        if is_external is not None:
            q = q.filter(SettlementInstructionModel.is_external == is_external)
        total = q.count()
        items = q.order_by(SettlementInstructionModel.lei, SettlementInstructionModel.currency).offset(offset).limit(limit).all()
        return items, total

    def get(self, lei: str, currency: str, is_external: bool = False) -> SettlementInstructionModel | None:
        return (
            self._db.query(SettlementInstructionModel)
            .filter(
                SettlementInstructionModel.lei == lei,
                SettlementInstructionModel.currency == currency,
                SettlementInstructionModel.is_external == is_external,
            )
            .first()
        )

    def register(self, ssi: SettlementInstruction, is_external: bool = False) -> None:
        """Insert or update an SSI record."""
        now = datetime.now(timezone.utc)
        existing = self.get(ssi.lei, ssi.currency, is_external)
        if existing is not None:
            existing.bic = ssi.bic
            existing.account = ssi.account
            existing.iban = ssi.iban
            existing.updated_at = now
        else:
            self._db.add(SettlementInstructionModel(
                id=uuid.uuid4(),
                lei=ssi.lei,
                currency=ssi.currency,
                bic=ssi.bic,
                account=ssi.account,
                iban=ssi.iban,
                is_external=is_external,
                created_at=now,
                updated_at=now,
            ))
        self._db.commit()

    @staticmethod
    def to_domain(row: SettlementInstructionModel) -> SettlementInstruction:
        return SettlementInstruction(
            lei=row.lei,
            currency=row.currency,
            bic=row.bic,
            account=row.account,
            iban=row.iban,
        )
