"""migrate subscriptions: add user_id FK, backfill from user_identity, drop bale_user_id

Revision ID: a1b2c3d4e505
Revises: a1b2c3d4e504
Create Date: 2026-05-14 11:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e505"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e504"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add nullable user_id for backfill, then make NOT NULL after population
    op.add_column("user_subscription", sa.Column("user_id", sa.String(length=36), nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE user_subscription us
        SET user_id = ui.user_id
        FROM user_identity ui
        WHERE ui.provider = 'bale'
          AND ui.provider_user_id = CAST(us.bale_user_id AS VARCHAR)
    """))

    # Make NOT NULL now that data is populated
    op.alter_column("user_subscription", "user_id", nullable=False)
    op.create_foreign_key("fk_subscription_user", "user_subscription", "user", ["user_id"], ["id"])
    op.create_index("ix_user_subscription_user_id", "user_subscription", ["user_id"], unique=True)

    # Drop bale_user_id
    op.drop_index("ix_user_subscription_bale_user_id", table_name="user_subscription")
    op.drop_column("user_subscription", "bale_user_id")


def downgrade() -> None:
    op.add_column(
        "user_subscription",
        sa.Column("bale_user_id", sa.BigInteger(), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE user_subscription us
        SET bale_user_id = CAST(ui.provider_user_id AS BIGINT)
        FROM user_identity ui
        WHERE ui.user_id = us.user_id AND ui.provider = 'bale'
    """))
    op.alter_column("user_subscription", "bale_user_id", nullable=False)
    op.create_index("ix_user_subscription_bale_user_id", "user_subscription", ["bale_user_id"], unique=True)

    op.drop_index("ix_user_subscription_user_id", table_name="user_subscription")
    op.drop_constraint("fk_subscription_user", "user_subscription", type_="foreignkey")
    op.drop_column("user_subscription", "user_id")
