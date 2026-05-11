"""add article language and homepage visibility toggles

Revision ID: b1d2e3f4a5b6
Revises: 9ebd2f7dfcf8
Create Date: 2026-05-09 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1d2e3f4a5b6'
down_revision = '9ebd2f7dfcf8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    article_columns = {c['name'] for c in inspector.get_columns('article')}
    project_columns = {c['name'] for c in inspector.get_columns('project')}

    if 'language_code' not in article_columns:
        op.add_column('article', sa.Column('language_code', sa.String(length=10), nullable=False, server_default='en'))
    if 'show_on_homepage' not in article_columns:
        op.add_column('article', sa.Column('show_on_homepage', sa.Boolean(), nullable=False, server_default=sa.true()))
    if 'show_on_homepage' not in project_columns:
        op.add_column('project', sa.Column('show_on_homepage', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('show_on_homepage')

    with op.batch_alter_table('article', schema=None) as batch_op:
        batch_op.drop_column('show_on_homepage')
        batch_op.drop_column('language_code')
