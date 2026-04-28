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
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
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


# ---------------------------------------------------------------------------
# Domain tables (trades, counterparties, SSI, reference data, STP exceptions)
# ---------------------------------------------------------------------------


class TradeModel(Base):
    """Trade master data with STP processing status and workflow state."""

    __tablename__ = "trades"
    __table_args__ = (
        UniqueConstraint("trade_id", "version", name="uq_trades_trade_id_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # WorkflowStatus: Initial / FoCheck / FoAgentToCheck / FoUserToValidate / FoValidated /
    #                 BoCheck / BoAgentToCheck / BoUserToValidate / BoValidated / Done /
    #                 Cancelled / EventPending
    workflow_status: Mapped[str] = mapped_column(String(30), nullable=False, default="Initial")
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    counterparty_lei: Mapped[str] = mapped_column(String(30), nullable=False)
    instrument_id: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 5), nullable=False)
    value_date: Mapped[date] = mapped_column(Date, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    settlement_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    sendback_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fo_check_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    bo_check_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    bo_sendback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fo_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CounterpartyModel(Base):
    """Counterparty master data."""

    __tablename__ = "counterparties"

    lei: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    bic: Mapped[str] = mapped_column(String(15), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SettlementInstructionModel(Base):
    """Settlement Standing Instruction (internal and external)."""

    __tablename__ = "settlement_instructions"
    __table_args__ = (
        UniqueConstraint("lei", "currency", "is_external", name="uq_ssi_lei_currency_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lei: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    bic: Mapped[str] = mapped_column(String(15), nullable=False)
    account: Mapped[str] = mapped_column(String(100), nullable=False)
    iban: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # False = internal SSI (registered), True = external SSI (lookup source)
    is_external: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReferenceDataModel(Base):
    """Instrument reference data."""

    __tablename__ = "reference_data"

    instrument_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class StpExceptionModel(Base):
    """STP exception record — one per failed trade."""

    __tablename__ = "stp_exceptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Soft reference to trades.trade_id (no FK constraint for flexibility)
    trade_id: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    # StpExceptionStatus: OPEN / IN_PROGRESS / RESOLVED / CLOSED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    # Soft reference to triage_runs.id — written back after triage starts
    triage_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class TradeEventModel(Base):
    """Trade event record — Amend or Cancel initiated on a trade."""

    __tablename__ = "trade_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Soft reference to trades.trade_id
    trade_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    from_version: Mapped[int] = mapped_column(Integer, nullable=False)
    to_version: Mapped[int] = mapped_column(Integer, nullable=False)
    # EventType: AMEND / CANCEL
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # EventWorkflowStatus: FoUserToValidate / FoValidated / BoUserToValidate / BoValidated / Done / Cancelled
    workflow_status: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    amended_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AppSettingModel(Base):
    """Application settings table — key/value store for configurable behaviour."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
