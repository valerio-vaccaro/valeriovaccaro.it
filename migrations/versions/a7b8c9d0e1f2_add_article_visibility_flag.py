"""add article visibility flag

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-09 23:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    article_columns = {c['name'] for c in inspector.get_columns('article')}
    if 'is_visible' not in article_columns:
        op.add_column('article', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_column('is_visible')
