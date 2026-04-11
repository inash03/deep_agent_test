"""initial schema

このファイルは Alembic の「マイグレーションファイル」。
Git のコミットのように、DBスキーマの変更を記録する。

  upgrade()   — このファイルを「適用」するときに実行される SQL 操作
  downgrade() — このファイルを「取り消す」ときに実行される SQL 操作

--autogenerate で生成した場合は models.py と DB の差分が自動で書かれる。
今回は最初のテーブル作成なので手動で記述している。

Revision ID: 0001
Revises: （なし — これが最初の migration）
Create Date: 2026-04-11
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None  # None = 最初の migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """triage_runs と triage_steps テーブルを作成する。

    Alembic は alembic_version テーブルでどこまで適用済みかを追跡する。
    適用後: alembic_version.version_num = "0001"
    """
    # ----------------------------------------------------------------
    # triage_runs — トリアージ実行の記録（1行 = 1回の実行）
    # ----------------------------------------------------------------
    op.create_table(
        "triage_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("trade_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        # LangGraph の thread_id（HITL 再開・UPDATE に使う検索キー）
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("pending_action_description", sa.Text(), nullable=True),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.String(50), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("action_taken", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    # run_id に index を貼る（resume 時の検索を高速化）
    op.create_index("ix_triage_runs_run_id", "triage_runs", ["run_id"])

    # ----------------------------------------------------------------
    # triage_steps — エージェントのステップ履歴（1行 = 1ツール呼び出し）
    # ----------------------------------------------------------------
    op.create_table(
        "triage_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column(
            "triage_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("triage_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("step_type", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        # JSONB: PostgreSQL のバイナリJSON型（検索・インデックス可能）
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    """upgrade() で作ったテーブルを削除する。

    alembic downgrade -1 で呼ばれる。
    外部キー制約があるため triage_steps を先に削除する必要がある。
    """
    op.drop_table("triage_steps")
    op.drop_index("ix_triage_runs_run_id", table_name="triage_runs")
    op.drop_table("triage_runs")
