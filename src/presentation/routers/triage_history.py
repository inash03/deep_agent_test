"""FastAPI router for triage run history.

Endpoint:
  GET /api/v1/triage/history — list recent FO/BO triage runs from DB
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.infrastructure.db.repository import TriageResultRepository
from src.infrastructure.db.session import get_db
from src.presentation.schemas import TriageHistoryResponse, TriageResponse

router = APIRouter(prefix="/api/v1", tags=["triage-history"])


@router.get(
    "/triage/history",
    response_model=TriageHistoryResponse,
    summary="List recent triage runs",
    description="Returns the most recent FO/BO triage runs stored in the database (newest first).",
)
def get_triage_history(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> TriageHistoryResponse:
    results = TriageResultRepository(db).list_recent(limit=limit)
    return TriageHistoryResponse(
        items=[TriageResponse.from_domain(r) for r in results],
        total=len(results),
    )
