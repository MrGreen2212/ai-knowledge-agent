"""Add text and embedding fields

Revision ID: ec90cfcc3d67
Revises: 
Create Date: 2026-07-14 11:03:08.486232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ec90cfcc3d67'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('text', sa.Text(), nullable=True))
    op.add_column(
        'documents',
        sa.Column('embedding', postgresql.ARRAY(postgresql.DOUBLE_PRECISION(precision=53)), nullable=True) # type: ignore
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
