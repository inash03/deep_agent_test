"""Drop stp_status column from trades table (technical debt removal)

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-28

Phase 26 introduced workflow_status (12 states) which fully supersedes
stp_status (NEW/STP_PASSED/STP_FAILED/SETTLED). The column is now redundant.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("trades", "stp_status")


def downgrade() -> None:
    op.add_column(
        "trades",
        sa.Column("stp_status", sa.String(20), nullable=False, server_default="NEW"),
    )
