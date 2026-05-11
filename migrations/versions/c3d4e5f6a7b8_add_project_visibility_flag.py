"""add project visibility flag

Revision ID: c3d4e5f6a7b8
Revises: b1d2e3f4a5b6
Create Date: 2026-05-09 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    project_columns = {c['name'] for c in inspector.get_columns('project')}
    if 'is_visible' not in project_columns:
        op.add_column('project', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('is_visible')
