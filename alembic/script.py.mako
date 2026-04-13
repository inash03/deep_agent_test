"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """スキーマ変更を適用する（alembic upgrade head で呼ばれる）。"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """スキーマ変更を取り消す（alembic downgrade -1 で呼ばれる）。"""
    ${downgrades if downgrades else "pass"}
