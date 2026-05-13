"""add total_paid_irr to user_subscription

Revision ID: e5a3c2d8f910
Revises: d4f2b8e9c100
Create Date: 2026-05-13 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5a3c2d8f910"
down_revision: Union[str, Sequence[str], None] = "d4f2b8e9c100"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("user_subscription")}
    if "total_paid_irr" not in cols:
        op.add_column(
            "user_subscription",
            sa.Column("total_paid_irr", sa.BigInteger(), nullable=False, server_default="0"),
        )
        op.execute(text("UPDATE user_subscription SET total_paid_irr = 0 WHERE total_paid_irr IS NULL"))


def downgrade() -> None:
    op.drop_column("user_subscription", "total_paid_irr")
