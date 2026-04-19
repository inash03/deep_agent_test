"""Repository for Reference Data (instruments)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.domain.entities import ReferenceData
from src.infrastructure.db.models import ReferenceDataModel


class ReferenceDataRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list(self) -> list[ReferenceDataModel]:
        return (
            self._db.query(ReferenceDataModel)
            .order_by(ReferenceDataModel.asset_class, ReferenceDataModel.instrument_id)
            .all()
        )

    def get_by_instrument_id(self, instrument_id: str) -> ReferenceDataModel | None:
        return (
            self._db.query(ReferenceDataModel)
            .filter(ReferenceDataModel.instrument_id == instrument_id)
            .first()
        )

    @staticmethod
    def to_domain(row: ReferenceDataModel) -> ReferenceData:
        return ReferenceData(
            instrument_id=row.instrument_id,
            description=row.description,
            asset_class=row.asset_class,
            is_active=row.is_active,
        )
