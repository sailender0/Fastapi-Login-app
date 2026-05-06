"""add profile fields

Revision ID: 2bd923468dcc
Revises: 4cb46ee3514f
Create Date: 2026-05-05 19:15:28.402858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bd923468dcc'
down_revision: Union[str, Sequence[str], None] = '4cb46ee3514f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. We skip the email alter/index because it already exists or is causing errors
    # op.alter_column('users', 'email', existing_type=sa.VARCHAR(length=255), nullable=False)
    
    # 2. Add the actual profile columns you need
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bio', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_image', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the columns if we need to roll back
    op.drop_column('users', 'profile_image')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'full_name')