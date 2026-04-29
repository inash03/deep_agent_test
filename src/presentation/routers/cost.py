"""Cost tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.infrastructure.db.llm_cost_log_repository import LlmCostLogRepository
from src.infrastructure.db.session import get_db
from src.presentation.schemas import (
    AgentCostBreakdown,
    CostLogListResponse,
    CostSummaryResponse,
    DailyCostOut,
    LlmCostLogOut,
    ModelCostBreakdown,
)

router = APIRouter(prefix="/api/v1/cost", tags=["cost"])


@router.get("/summary", response_model=CostSummaryResponse, summary="LLM cost summary")
def get_cost_summary(
    days: int = Query(default=30, ge=1, le=365, description="Daily breakdown window (days)"),
    db: Session = Depends(get_db),
) -> CostSummaryResponse:
    repo = LlmCostLogRepository(db)
    summary = repo.get_summary()
    daily = repo.get_daily_costs(days=days)
    return CostSummaryResponse(
        total_cost_usd=summary["total_cost_usd"],
        total_input_tokens=summary["total_input_tokens"],
        total_output_tokens=summary["total_output_tokens"],
        total_calls=summary["total_calls"],
        total_runs=summary["total_runs"],
        by_agent=[AgentCostBreakdown(**a) for a in summary["by_agent"]],
        by_model=[ModelCostBreakdown(**m) for m in summary["by_model"]],
        daily_costs=[DailyCostOut(**d) for d in daily],
    )


@router.get("/logs", response_model=CostLogListResponse, summary="Recent LLM cost log entries")
def list_cost_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> CostLogListResponse:
    repo = LlmCostLogRepository(db)
    rows = repo.list_recent(limit=limit)
    items = [
        LlmCostLogOut(
            id=r.id,
            run_id=r.run_id,
            trade_id=r.trade_id,
            agent_type=r.agent_type,
            node=r.node,
            model=r.model,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            cost_usd=float(r.cost_usd),
            reason=r.reason,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return CostLogListResponse(items=items, total=len(items))
