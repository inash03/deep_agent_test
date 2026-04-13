"""FastAPI router for the STP Exception Triage Agent.

Endpoints:
  POST /api/v1/triage                    — start a new triage run
  POST /api/v1/triage/{run_id}/resume    — resume a PENDING_APPROVAL run
  GET  /api/v1/triage/history            — list recent triage runs from DB
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.domain.entities import STPFailure
from src.domain.interfaces import ITriageUseCase
from src.infrastructure.db.repository import TriageResultRepository
from src.infrastructure.db.session import get_db
from src.infrastructure.triage_use_case import TriageSTPFailureUseCase
from src.presentation.schemas import (
    ResumeRequest,
    TriageHistoryResponse,
    TriageRequest,
    TriageResponse,
)

router = APIRouter(prefix="/api/v1")

# ---------------------------------------------------------------------------
# Dependency — singleton use case (MemorySaver must persist across requests)
# ---------------------------------------------------------------------------

_use_case: ITriageUseCase | None = None


def get_use_case() -> ITriageUseCase:
    global _use_case
    if _use_case is None:
        _use_case = TriageSTPFailureUseCase()
    return _use_case


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/triage",
    response_model=TriageResponse,
    summary="Start STP exception triage",
    description=(
        "Launches the ReAct agent to investigate the given STP failure. "
        "Returns COMPLETED with a diagnosis, or PENDING_APPROVAL with a "
        "run_id when the agent needs to register an SSI and awaits operator approval."
    ),
)
def start_triage(
    body: TriageRequest,
    use_case: ITriageUseCase = Depends(get_use_case),
    db: Session = Depends(get_db),
) -> TriageResponse:
    failure = STPFailure(trade_id=body.trade_id, error_message=body.error_message)
    result = use_case.start(failure)
    # エージェントの実行結果を DB に永続化する
    # use_case は純粋なビジネスロジック（DB を知らない）
    # router がユースケース呼び出し後に永続化を担当する
    TriageResultRepository(db).save(result)
    return TriageResponse.from_domain(result)


@router.post(
    "/triage/{run_id}/resume",
    response_model=TriageResponse,
    summary="Resume a PENDING_APPROVAL triage run",
    description=(
        "Resumes a triage run that is waiting for operator approval. "
        "Set approved=true to allow the pending action (e.g. SSI registration), "
        "or approved=false to skip it and receive the diagnosis only."
    ),
)
def resume_triage(
    run_id: str,
    body: ResumeRequest,
    use_case: ITriageUseCase = Depends(get_use_case),
    db: Session = Depends(get_db),
) -> TriageResponse:
    try:
        result = use_case.resume(run_id, approved=body.approved)
    except StopIteration:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found or already completed.",
        )
    # COMPLETED に更新された結果を DB に upsert（既存レコードを UPDATE）
    TriageResultRepository(db).save(result)
    return TriageResponse.from_domain(result)


@router.get(
    "/triage/history",
    response_model=TriageHistoryResponse,
    summary="List recent triage runs",
    description="Returns the most recent triage runs stored in the database (newest first).",
)
def get_triage_history(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> TriageHistoryResponse:
    """DB に保存されたトリアージ履歴を返す。

    これが Alembic で作ったテーブルへの実際の読み取りクエリ。
    TriageResultRepository.list_recent() が SELECT ... ORDER BY created_at DESC を発行する。
    """
    results = TriageResultRepository(db).list_recent(limit=limit)
    return TriageHistoryResponse(
        items=[TriageResponse.from_domain(r) for r in results],
        total=len(results),
    )
