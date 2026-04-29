"""Repository for LLM cost log data."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.infrastructure.db.models import LlmCostLogModel


class LlmCostLogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_batch(
        self,
        entries: list[dict],
        run_id: str,
        trade_id: str,
        agent_type: str,
    ) -> None:
        """Save a list of cost_log dicts from agent state to the DB."""
        for entry in entries:
            # model_router entries have cost_usd=0 and no real token counts — skip
            if entry.get("node") == "model_router" and entry.get("cost_usd", 0) == 0:
                continue
            row = LlmCostLogModel(
                id=uuid.uuid4(),
                run_id=run_id,
                trade_id=trade_id or None,
                agent_type=agent_type,
                node=entry.get("node", "unknown"),
                model=entry.get("model", "unknown"),
                input_tokens=int(entry.get("input_tokens", 0)),
                output_tokens=int(entry.get("output_tokens", 0)),
                cost_usd=Decimal(str(entry.get("cost_usd", 0))),
                reason=entry.get("reason"),
                created_at=_parse_ts(entry.get("timestamp")),
            )
            self._db.add(row)
        self._db.flush()

    def get_summary(self) -> dict:
        """Return aggregate cost statistics across all recorded runs."""
        row = self._db.query(
            func.coalesce(func.sum(LlmCostLogModel.cost_usd), 0).label("total_cost"),
            func.coalesce(func.sum(LlmCostLogModel.input_tokens), 0).label("total_input"),
            func.coalesce(func.sum(LlmCostLogModel.output_tokens), 0).label("total_output"),
            func.count(LlmCostLogModel.id).label("total_calls"),
            func.count(func.distinct(LlmCostLogModel.run_id)).label("total_runs"),
        ).one()

        by_agent = self._db.query(
            LlmCostLogModel.agent_type,
            func.coalesce(func.sum(LlmCostLogModel.cost_usd), 0).label("cost_usd"),
            func.count(func.distinct(LlmCostLogModel.run_id)).label("run_count"),
            func.count(LlmCostLogModel.id).label("call_count"),
        ).group_by(LlmCostLogModel.agent_type).all()

        by_model = self._db.query(
            LlmCostLogModel.model,
            func.coalesce(func.sum(LlmCostLogModel.cost_usd), 0).label("cost_usd"),
            func.count(LlmCostLogModel.id).label("call_count"),
        ).group_by(LlmCostLogModel.model).all()

        return {
            "total_cost_usd": float(row.total_cost),
            "total_input_tokens": int(row.total_input),
            "total_output_tokens": int(row.total_output),
            "total_calls": int(row.total_calls),
            "total_runs": int(row.total_runs),
            "by_agent": [
                {
                    "agent_type": r.agent_type,
                    "cost_usd": float(r.cost_usd),
                    "run_count": int(r.run_count),
                    "call_count": int(r.call_count),
                }
                for r in by_agent
            ],
            "by_model": [
                {
                    "model": r.model,
                    "cost_usd": float(r.cost_usd),
                    "call_count": int(r.call_count),
                }
                for r in by_model
            ],
        }

    def get_daily_costs(self, days: int = 30) -> list[dict]:
        """Return daily cost totals for the last *days* days."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            self._db.query(
                func.date(LlmCostLogModel.created_at).label("day"),
                func.coalesce(func.sum(LlmCostLogModel.cost_usd), 0).label("cost_usd"),
                func.count(func.distinct(LlmCostLogModel.run_id)).label("run_count"),
                func.count(LlmCostLogModel.id).label("call_count"),
            )
            .filter(LlmCostLogModel.created_at >= since)
            .group_by(text("day"))
            .order_by(text("day"))
            .all()
        )
        return [
            {
                "date": str(r.day),
                "cost_usd": float(r.cost_usd),
                "run_count": int(r.run_count),
                "call_count": int(r.call_count),
            }
            for r in rows
        ]

    def list_recent(self, limit: int = 100) -> list[LlmCostLogModel]:
        return (
            self._db.query(LlmCostLogModel)
            .order_by(LlmCostLogModel.created_at.desc())
            .limit(limit)
            .all()
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.now(timezone.utc)
