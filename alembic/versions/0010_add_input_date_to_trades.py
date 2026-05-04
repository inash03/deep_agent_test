"""add input date to trades

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("input_date", sa.Date(), nullable=True))
    op.execute("UPDATE trades SET input_date = trade_date WHERE input_date IS NULL")
    op.alter_column("trades", "input_date", nullable=False)


def downgrade() -> None:
    op.drop_column("trades", "input_date")
