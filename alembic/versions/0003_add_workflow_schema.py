"""add workflow schema: version management, WorkflowStatus, TradeEvents, AppSettings

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # trades — PK を UUID id に変更 + ワークフローカラム追加
    # ----------------------------------------------------------------

    # 1. Add id UUID column (nullable first so existing rows are accepted)
    op.add_column("trades", sa.Column("id", postgresql.UUID(as_uuid=True), nullable=True))

    # 2. Populate id for all existing rows
    op.execute("UPDATE trades SET id = gen_random_uuid()")

    # 3. Set NOT NULL
    op.alter_column("trades", "id", nullable=False)

    # 4. Drop old primary key on trade_id
    op.drop_constraint("trades_pkey", "trades", type_="primary")

    # 5. Create new primary key on id
    op.create_primary_key("trades_pkey", "trades", ["id"])

    # 6. Index on trade_id (formerly the PK — queries still filter by it)
    op.create_index("ix_trades_trade_id", "trades", ["trade_id"])

    # 7. Add version column (server_default sets 1 for all existing rows)
    op.add_column(
        "trades",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    # 8. Unique constraint on (trade_id, version)
    op.create_unique_constraint("uq_trades_trade_id_version", "trades", ["trade_id", "version"])

    # 9. Add is_current column
    op.add_column(
        "trades",
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
    )

    # 10. Add workflow_status (default: Initial for all existing rows)
    op.add_column(
        "trades",
        sa.Column("workflow_status", sa.String(30), nullable=False, server_default="Initial"),
    )
    # Existing STP_FAILED trades are at the FoAgentToCheck stage
    op.execute(
        "UPDATE trades SET workflow_status = 'FoAgentToCheck' WHERE stp_status = 'STP_FAILED'"
    )

    # 11. Add sendback_count
    op.add_column(
        "trades",
        sa.Column("sendback_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 12. Add JSONB check result columns
    op.add_column(
        "trades",
        sa.Column("fo_check_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "trades",
        sa.Column("bo_check_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # 13. Add text columns for agent communication
    op.add_column("trades", sa.Column("bo_sendback_reason", sa.Text(), nullable=True))
    op.add_column("trades", sa.Column("fo_explanation", sa.Text(), nullable=True))

    # ----------------------------------------------------------------
    # trade_events — Amend / Cancel イベント
    # ----------------------------------------------------------------
    op.create_table(
        "trade_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trade_id", sa.String(50), nullable=False),
        sa.Column("from_version", sa.Integer(), nullable=False),
        sa.Column("to_version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(10), nullable=False),
        sa.Column("workflow_status", sa.String(30), nullable=False),
        sa.Column("requested_by", sa.String(100), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("amended_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trade_events_trade_id", "trade_events", ["trade_id"])

    # ----------------------------------------------------------------
    # app_settings — アプリケーション設定（auto/manual トリガーなど）
    # ----------------------------------------------------------------
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(100), primary_key=True, nullable=False),
        sa.Column("value", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Insert default settings
    op.execute(
        """
        INSERT INTO app_settings (key, value, description, updated_at) VALUES
        ('fo_check_trigger', 'manual',
         'Trigger mode for FoCheck: auto (run on Initial entry) or manual', NOW()),
        ('bo_check_trigger', 'manual',
         'Trigger mode for BoCheck: auto (run on FoValidated entry) or manual', NOW())
        """
    )


def downgrade() -> None:
    op.drop_table("app_settings")

    op.drop_index("ix_trade_events_trade_id", table_name="trade_events")
    op.drop_table("trade_events")

    # Revert trades columns
    op.drop_column("trades", "fo_explanation")
    op.drop_column("trades", "bo_sendback_reason")
    op.drop_column("trades", "bo_check_results")
    op.drop_column("trades", "fo_check_results")
    op.drop_column("trades", "sendback_count")
    op.drop_column("trades", "workflow_status")
    op.drop_column("trades", "is_current")
    op.drop_constraint("uq_trades_trade_id_version", "trades", type_="unique")
    op.drop_column("trades", "version")
    op.drop_index("ix_trades_trade_id", table_name="trades")

    # Restore original PK on trade_id
    op.drop_constraint("trades_pkey", "trades", type_="primary")
    op.create_primary_key("trades_pkey", "trades", ["trade_id"])
    op.drop_column("trades", "id")
