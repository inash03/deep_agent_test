"""SQLAlchemy ORM models for the STP Exception Triage Agent.

テーブル構成:
  triage_runs  — TriageResult の永続化（1行 = 1回のトリアージ実行）
  triage_steps — 各実行中のエージェントのステップ（ツール呼び出し履歴）

NOTE: これらは「SQLAlchemyモデル」= DBテーブルの定義。
      ドメインエンティティ（entities.py）とは別物。
      相互変換は repository.py が担当する。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """全モデルの共通基底クラス。Alembic がこの metadata を参照する。"""


class TriageRunModel(Base):
    """1回のトリアージ実行を表すテーブル。

    Columns:
      id                          — DB 内部 UUID（PK）
      trade_id                    — 調査対象のトレード ID
      status                      — COMPLETED / PENDING_APPROVAL
      run_id                      — LangGraph の thread_id（HITL 再開用）
      pending_action_description  — HITL 承認待ちの場合の説明文
      diagnosis                   — LLM による診断文
      root_cause                  — 根本原因 enum 値（文字列）
      recommended_action          — 推奨アクション
      action_taken                — register_ssi が実行されたか
      created_at / updated_at     — 監査用タイムスタンプ
    """

    __tablename__ = "triage_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trade_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    pending_action_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 1対多: 1つの triage_run に複数の steps
    steps: Mapped[list[TriageStepModel]] = relationship(
        "TriageStepModel",
        back_populates="triage_run",
        order_by="TriageStepModel.position",
        cascade="all, delete-orphan",  # run を削除すると steps も自動削除
    )


class TriageStepModel(Base):
    """エージェントの1ステップ（ツール呼び出し or HITL イベント）。

    Columns:
      id             — 自動採番 PK
      triage_run_id  — 親の triage_runs.id（FK）
      position       — ステップの順序（0始まり）
      step_type      — "tool_call" / "hitl_prompt" / "hitl_response"
      name           — ツール名（例: "get_trade_detail"）
      input          — ツールへの引数（JSONB）
      output         — ツールの返り値（JSONB、HITL 承認待ち中は NULL）
      approved       — HITL の承認結果（tool_call では NULL）
    """

    __tablename__ = "triage_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    triage_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("triage_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    triage_run: Mapped[TriageRunModel] = relationship(
        "TriageRunModel", back_populates="steps"
    )
