"""add user bale_user_id

Revision ID: b7c91e2f4d10
Revises: a6f4f8a26d20
Create Date: 2026-05-09 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c91e2f4d10"
down_revision: Union[str, Sequence[str], None] = "a6f4f8a26d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("user", sa.Column("bale_user_id", sa.BigInteger(), nullable=True))
    op.create_index(
        op.f("ix_user_bale_user_id"),
        "user",
        ["bale_user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_user_bale_user_id"), table_name="user")
    op.drop_column("user", "bale_user_id")
