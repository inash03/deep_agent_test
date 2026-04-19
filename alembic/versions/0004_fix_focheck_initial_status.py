"""Fix FoCheck initial workflow_status: FoAgentToCheck → FoCheck for unchecked trades

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-19

Migration 0003 incorrectly set workflow_status='FoAgentToCheck' for all STP_FAILED
trades, but FoAgentToCheck means "FoCheck was run and found errors; agent must
investigate." Trades that have never had FoCheck run should be in 'FoCheck' status
(awaiting check execution).
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only fix rows where FoCheck has never been executed (fo_check_results IS NULL).
    # Rows that legitimately reached FoAgentToCheck after a real check run are untouched.
    op.execute(
        """
        UPDATE trades
        SET workflow_status = 'FoCheck'
        WHERE workflow_status = 'FoAgentToCheck'
          AND fo_check_results IS NULL
        """
    )


def downgrade() -> None:
    # Restore to the (incorrect) previous state for rollback completeness.
    op.execute(
        """
        UPDATE trades
        SET workflow_status = 'FoAgentToCheck'
        WHERE workflow_status = 'FoCheck'
          AND fo_check_results IS NULL
          AND stp_status = 'STP_FAILED'
        """
    )
