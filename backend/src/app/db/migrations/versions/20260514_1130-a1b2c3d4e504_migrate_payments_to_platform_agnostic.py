"""migrate payments: create payment table with user_id FK, backfill, drop bale_payment

Revision ID: a1b2c3d4e504
Revises: a1b2c3d4e503
Create Date: 2026-05-14 11:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e504"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e503"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column("plan_key", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="IRR"),
        sa.Column("invoice_payload", sa.String(length=256), nullable=False),
        sa.Column("provider_payment_charge_id", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_user_id", "payment", ["user_id"])

    # Backfill: resolve bale_user_id → user_id via user_identity
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO payment (id, user_id, provider, status, plan_key, amount, currency,
                             invoice_payload, provider_payment_charge_id, created_at, updated_at)
        SELECT p.id,
               ui.user_id,
               'bale',
               'success',
               p.plan_key,
               p.amount,
               p.currency,
               p.invoice_payload,
               p.provider_payment_charge_id,
               p.created_at,
               p.updated_at
        FROM bale_payment p
        JOIN user_identity ui
          ON ui.provider = 'bale'
         AND ui.provider_user_id = CAST(p.bale_user_id AS VARCHAR)
    """))

    op.drop_table("bale_payment")


def downgrade() -> None:
    op.create_table(
        "bale_payment",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bale_user_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_key", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("invoice_payload", sa.String(length=256), nullable=False),
        sa.Column("provider_payment_charge_id", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO bale_payment (id, bale_user_id, plan_key, amount, currency,
                                  invoice_payload, provider_payment_charge_id, created_at, updated_at)
        SELECT p.id,
               CAST(ui.provider_user_id AS BIGINT),
               p.plan_key, p.amount, p.currency,
               p.invoice_payload, p.provider_payment_charge_id,
               p.created_at, p.updated_at
        FROM payment p
        JOIN user_identity ui ON ui.user_id = p.user_id AND ui.provider = 'bale'
        WHERE p.provider = 'bale'
    """))

    op.drop_index("ix_payment_user_id", table_name="payment")
    op.drop_table("payment")
