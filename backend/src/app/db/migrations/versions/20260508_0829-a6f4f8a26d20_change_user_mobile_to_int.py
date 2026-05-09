"""change_user_mobile_to_int

Revision ID: a6f4f8a26d20
Revises: 30467773703d
Create Date: 2026-05-08 08:29:02.387896

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6f4f8a26d20'
down_revision: Union[str, Sequence[str], None] = '30467773703d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('user', 'mobile',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.BigInteger(),
               existing_nullable=False,
               postgresql_using='mobile::bigint')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('user', 'mobile',
               existing_type=sa.BigInteger(),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
