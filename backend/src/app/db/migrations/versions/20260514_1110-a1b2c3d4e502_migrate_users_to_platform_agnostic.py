"""migrate users to platform-agnostic: add email, backfill user_identity, drop bale_user_id

Revision ID: a1b2c3d4e502
Revises: a1b2c3d4e501
Create Date: 2026-05-14 11:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e502"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e501"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email column to users
    op.add_column("user", sa.Column("email", sa.String(length=255), nullable=True))
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    # Backfill user_identity from users.bale_user_id (idempotent: skip NULLs and existing rows)
    conn = op.get_bind()
    import uuid as _uuid
    from datetime import datetime, timezone

    rows = conn.execute(
        sa.text("SELECT id, bale_user_id FROM \"user\" WHERE bale_user_id IS NOT NULL")
    ).fetchall()
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    for row in rows:
        user_id, bale_user_id = row[0], row[1]
        existing = conn.execute(
            sa.text(
                "SELECT id FROM user_identity WHERE provider = 'bale' AND provider_user_id = :pid"
            ),
            {"pid": str(bale_user_id)},
        ).first()
        if existing is None:
            conn.execute(
                sa.text(
                    "INSERT INTO user_identity (id, user_id, provider, provider_user_id, created_at, updated_at) "
                    "VALUES (:id, :user_id, 'bale', :pid, :now, :now)"
                ),
                {"id": str(_uuid.uuid4()), "user_id": user_id, "pid": str(bale_user_id), "now": now},
            )

    # Drop bale_user_id from users
    op.drop_index("ix_user_bale_user_id", table_name="user")
    op.drop_column("user", "bale_user_id")


def downgrade() -> None:
    op.add_column(
        "user",
        sa.Column("bale_user_id", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_user_bale_user_id", "user", ["bale_user_id"], unique=True)
    # Restore bale_user_id from user_identity
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT user_id, provider_user_id FROM user_identity WHERE provider = 'bale'")
    ).fetchall()
    for row in rows:
        user_id, provider_user_id = row[0], row[1]
        conn.execute(
            sa.text("UPDATE \"user\" SET bale_user_id = :bid WHERE id = :uid"),
            {"bid": int(provider_user_id), "uid": user_id},
        )
    op.drop_index("ix_user_email", table_name="user")
    op.drop_column("user", "email")
