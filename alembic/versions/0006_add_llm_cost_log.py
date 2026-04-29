"""Add llm_cost_logs table for LLM cost tracking

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-29

Each row records one LLM call made by FoAgent or BoAgent.
Enables cost-summary API and CostPage frontend.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_cost_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("trade_id", sa.String(50), nullable=True),
        sa.Column("agent_type", sa.String(10), nullable=False),
        sa.Column("node", sa.String(100), nullable=False),
        sa.Column("model", sa.String(60), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_llm_cost_logs_run_id", "llm_cost_logs", ["run_id"])
    op.create_index("ix_llm_cost_logs_trade_id", "llm_cost_logs", ["trade_id"])


def downgrade() -> None:
    op.drop_index("ix_llm_cost_logs_trade_id", table_name="llm_cost_logs")
    op.drop_index("ix_llm_cost_logs_run_id", table_name="llm_cost_logs")
    op.drop_table("llm_cost_logs")
