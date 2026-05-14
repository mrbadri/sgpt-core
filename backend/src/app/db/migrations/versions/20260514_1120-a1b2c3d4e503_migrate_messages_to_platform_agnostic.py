"""migrate messages: create message table, backfill from bale_message, drop bale_message

Revision ID: a1b2c3d4e503
Revises: a1b2c3d4e502
Create Date: 2026-05-14 11:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e503"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e502"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_update_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_user_id", "message", ["user_id"])

    # Backfill from bale_message using existing user_id FK (already populated in prior migration)
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO message (id, user_id, channel, direction, message_type, content, raw_update_id, created_at, updated_at)
        SELECT id, user_id, 'bale', direction, message_type, content, raw_update_id, created_at, updated_at
        FROM bale_message
    """))

    # Drop old table
    op.drop_constraint("bale_message_user_id_fkey", "bale_message", type_="foreignkey")
    op.drop_index("ix_bale_message_user_id", table_name="bale_message")
    op.drop_table("bale_message")


def downgrade() -> None:
    op.create_table(
        "bale_message",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("bale_user_id", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("message_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("raw_update_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bale_message_user_id", "bale_message", ["user_id"])

    conn = op.get_bind()
    # Re-populate bale_user_id from user_identity
    conn.execute(sa.text("""
        INSERT INTO bale_message (id, user_id, bale_user_id, direction, message_type, content, raw_update_id, created_at, updated_at)
        SELECT m.id, m.user_id,
               CAST(ui.provider_user_id AS BIGINT),
               m.direction, m.message_type, m.content, m.raw_update_id, m.created_at, m.updated_at
        FROM message m
        LEFT JOIN user_identity ui ON ui.user_id = m.user_id AND ui.provider = 'bale'
        WHERE m.channel = 'bale'
    """))

    op.drop_index("ix_message_user_id", table_name="message")
    op.drop_table("message")
