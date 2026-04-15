"""add domain tables: trades, counterparties, settlement_instructions, reference_data, stp_exceptions

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-15
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # trades — 取引マスタ（STP ステータス付き）
    # ----------------------------------------------------------------
    op.create_table(
        "trades",
        sa.Column("trade_id", sa.String(50), primary_key=True, nullable=False),
        sa.Column("counterparty_lei", sa.String(30), nullable=False),
        sa.Column("instrument_id", sa.String(50), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(20, 5), nullable=False),
        sa.Column("value_date", sa.Date(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("settlement_currency", sa.String(10), nullable=False),
        # TradeStatus: NEW / STP_PASSED / STP_FAILED / SETTLED
        sa.Column("stp_status", sa.String(20), nullable=False, server_default="NEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trades_stp_status", "trades", ["stp_status"])
    op.create_index("ix_trades_trade_date", "trades", ["trade_date"])

    # ----------------------------------------------------------------
    # counterparties — カウンターパーティマスタ
    # ----------------------------------------------------------------
    op.create_table(
        "counterparties",
        sa.Column("lei", sa.String(30), primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("bic", sa.String(15), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ----------------------------------------------------------------
    # settlement_instructions — SSI（内部 / 外部）
    # ----------------------------------------------------------------
    op.create_table(
        "settlement_instructions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("lei", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("bic", sa.String(15), nullable=False),
        sa.Column("account", sa.String(100), nullable=False),
        sa.Column("iban", sa.String(50), nullable=True),
        # False = 内部登録済み SSI / True = 外部照会用 SSI
        sa.Column("is_external", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("lei", "currency", "is_external", name="uq_ssi_lei_currency_external"),
    )

    # ----------------------------------------------------------------
    # reference_data — 商品マスタ（FX通貨ペアなど）
    # ----------------------------------------------------------------
    op.create_table(
        "reference_data",
        sa.Column("instrument_id", sa.String(50), primary_key=True, nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("asset_class", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ----------------------------------------------------------------
    # stp_exceptions — STP 例外レコード（取引ごとに1件）
    # ----------------------------------------------------------------
    op.create_table(
        "stp_exceptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # trades.trade_id へのソフト参照（FK 制約なし）
        sa.Column("trade_id", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        # StpExceptionStatus: OPEN / IN_PROGRESS / RESOLVED / CLOSED
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        # triage_runs.id へのソフト参照（トリアージ開始後に書き戻す）
        sa.Column("triage_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stp_exceptions_trade_id", "stp_exceptions", ["trade_id"])
    op.create_index("ix_stp_exceptions_status", "stp_exceptions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_stp_exceptions_status", table_name="stp_exceptions")
    op.drop_index("ix_stp_exceptions_trade_id", table_name="stp_exceptions")
    op.drop_table("stp_exceptions")
    op.drop_table("reference_data")
    op.drop_table("settlement_instructions")
    op.drop_table("counterparties")
    op.drop_index("ix_trades_trade_date", table_name="trades")
    op.drop_index("ix_trades_stp_status", table_name="trades")
    op.drop_table("trades")
