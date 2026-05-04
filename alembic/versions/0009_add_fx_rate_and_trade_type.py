"""add fx rate and trade type to trades

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trades", sa.Column("fx_rate", sa.Numeric(20, 8), nullable=True))
    op.add_column("trades", sa.Column("trade_type", sa.String(10), nullable=True))

    op.execute(
        """
        UPDATE trades
        SET fx_rate = CASE
            WHEN instrument_id IN ('USD/JPY', 'USDJPY') THEN 151.25000000
            WHEN instrument_id IN ('EUR/USD', 'EURUSD') THEN 1.08500000
            WHEN instrument_id IN ('GBP/USD', 'GBPUSD') THEN 1.26500000
            WHEN instrument_id IN ('AUD/USD', 'AUDUSD') THEN 0.65500000
            ELSE 1.00000000
        END
        WHERE fx_rate IS NULL
        """
    )
    op.execute(
        """
        UPDATE trades
        SET trade_type = CASE
            WHEN (
                SELECT count(*)
                FROM generate_series(trade_date + interval '1 day', value_date, interval '1 day') AS d(day)
                WHERE extract(isodow FROM d.day) < 6
            ) > 2 THEN 'Forward'
            ELSE 'Spot'
        END
        WHERE trade_type IS NULL
        """
    )

    op.alter_column("trades", "fx_rate", nullable=False)
    op.alter_column("trades", "trade_type", nullable=False)


def downgrade() -> None:
    op.drop_column("trades", "trade_type")
    op.drop_column("trades", "fx_rate")
