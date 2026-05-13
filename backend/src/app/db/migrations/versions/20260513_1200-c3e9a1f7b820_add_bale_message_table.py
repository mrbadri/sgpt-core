"""add bale_message table

Revision ID: c3e9a1f7b820
Revises: b7c91e2f4d10
Create Date: 2026-05-13 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e9a1f7b820"
down_revision: Union[str, Sequence[str], None] = "08b674dcaa3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from alembic import op as _op
    from sqlalchemy import inspect
    bind = _op.get_bind()
    if "bale_message" in inspect(bind).get_table_names():
        return
    op.create_table(
        "bale_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bale_user_id", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_update_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bale_message_id", "bale_message", ["id"])
    op.create_index("ix_bale_message_bale_user_id", "bale_message", ["bale_user_id"])


def downgrade() -> None:
    op.drop_index("ix_bale_message_bale_user_id", table_name="bale_message")
    op.drop_index("ix_bale_message_id", table_name="bale_message")
    op.drop_table("bale_message")
