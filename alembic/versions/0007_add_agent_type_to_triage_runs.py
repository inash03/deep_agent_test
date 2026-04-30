"""Add agent_type column to triage_runs

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "triage_runs",
        sa.Column("agent_type", sa.String(10), nullable=False, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("triage_runs", "agent_type")
