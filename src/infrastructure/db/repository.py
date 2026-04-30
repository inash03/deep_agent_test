"""TriageResult の DB 永続化・取得を担当するリポジトリ。

Clean Architecture での位置づけ:
  Infrastructure 層 → Domain 層のエンティティを DB モデルに変換して保存する。

責務:
  save(result)     — TriageResult を DB に upsert（run_id で既存レコードを検索）
  list_recent(n)   — 最新 n 件の TriageResult を返す

NOTE: このクラスは1リクエスト1インスタンスで使うことを想定している。
      Session の ライフサイクル管理は呼び出し元（router）が行う。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.domain.entities import RootCause, Step, TriageResult, TriageStatus
from src.infrastructure.db.models import TriageRunModel, TriageStepModel


class TriageResultRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, result: TriageResult) -> None:
        """TriageResult を DB に保存する。

        - run_id が一致する既存レコードがあれば UPDATE（resume 後の完了記録）
        - なければ INSERT（新規実行の記録）

        Alembic の migration で作ったテーブルに対して操作する。
        """
        existing = (
            self._db.query(TriageRunModel)
            .filter(TriageRunModel.run_id == result.run_id)
            .first()
            if result.run_id
            else None
        )

        if existing is not None:
            self._update_run(existing, result)
        else:
            self._insert_run(result)

        self._db.commit()

    def _insert_run(self, result: TriageResult) -> None:
        run = TriageRunModel(
            trade_id=result.trade_id,
            status=result.status.value,
            run_id=result.run_id,
            pending_action_description=result.pending_action_description,
            diagnosis=result.diagnosis,
            root_cause=result.root_cause.value if result.root_cause else None,
            recommended_action=result.recommended_action,
            action_taken=result.action_taken,
            agent_type=result.agent_type,
            steps=[_step_to_model(s, pos) for pos, s in enumerate(result.steps)],
        )
        self._db.add(run)

    def _update_run(self, run: TriageRunModel, result: TriageResult) -> None:
        """PENDING_APPROVAL → COMPLETED への状態遷移を DB に反映する。"""
        run.status = result.status.value
        run.pending_action_description = result.pending_action_description
        run.diagnosis = result.diagnosis
        run.root_cause = result.root_cause.value if result.root_cause else None
        run.recommended_action = result.recommended_action
        run.action_taken = result.action_taken
        run.updated_at = datetime.now(timezone.utc)

        # 既存の steps を削除して再挿入（cascade="all, delete-orphan" で自動削除される）
        run.steps.clear()
        for pos, step in enumerate(result.steps):
            run.steps.append(_step_to_model(step, pos))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_recent(self, limit: int = 20) -> list[TriageResult]:
        """最新 limit 件のトリアージ結果を返す（新しい順）。"""
        runs = (
            self._db.query(TriageRunModel)
            .order_by(TriageRunModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_run_to_domain(run) for run in runs]


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _step_to_model(step: Step, position: int) -> TriageStepModel:
    return TriageStepModel(
        position=position,
        step_type=step.step_type,
        name=step.name,
        input=step.input,
        output=step.output,
        approved=step.approved,
    )


def _run_to_domain(run: TriageRunModel) -> TriageResult:
    """TriageRunModel（DB行）→ TriageResult（ドメインエンティティ）変換。"""
    return TriageResult(
        trade_id=run.trade_id,
        status=TriageStatus(run.status),
        run_id=run.run_id,
        pending_action_description=run.pending_action_description,
        diagnosis=run.diagnosis,
        root_cause=RootCause(run.root_cause) if run.root_cause else None,
        recommended_action=run.recommended_action,
        action_taken=run.action_taken,
        agent_type=run.agent_type,
        steps=[
            Step(
                step_type=s.step_type,
                name=s.name,
                input=s.input,
                output=s.output,
                approved=s.approved,
            )
            for s in run.steps  # relationship は position 順にソート済み
        ],
    )
