"""add user_subscription table

Revision ID: d4f2b8e9c100
Revises: c3e9a1f7b820
Create Date: 2026-05-13 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4f2b8e9c100"
down_revision: Union[str, Sequence[str], None] = "c3e9a1f7b820"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    bind = op.get_bind()
    if "user_subscription" in inspect(bind).get_table_names():
        return
    op.create_table(
        "user_subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bale_user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_key", sa.String(length=16), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("budget_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("used_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bale_user_id"),
    )
    op.create_index("ix_user_subscription_id", "user_subscription", ["id"])
    op.create_index("ix_user_subscription_bale_user_id", "user_subscription", ["bale_user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_subscription_bale_user_id", table_name="user_subscription")
    op.drop_index("ix_user_subscription_id", table_name="user_subscription")
    op.drop_table("user_subscription")
