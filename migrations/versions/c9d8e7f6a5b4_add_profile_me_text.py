"""add profile me text

Revision ID: c9d8e7f6a5b4
Revises: a7b8c9d0e1f2
Create Date: 2026-05-10 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d8e7f6a5b4'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    profile_columns = {c['name'] for c in inspector.get_columns('profile')}
    if 'markdown_me' not in profile_columns:
        op.add_column(
            'profile',
            sa.Column(
                'markdown_me',
                sa.Text(),
                nullable=False,
                server_default='Write your long About Me page in Markdown',
            ),
        )

    op.execute("UPDATE profile SET markdown_me = markdown_bio WHERE markdown_me IS NULL OR markdown_me = ''")


def downgrade():
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.drop_column('markdown_me')
