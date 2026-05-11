"""add project repository stats

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-09 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    project_columns = {c['name'] for c in inspector.get_columns('project')}

    add_specs = [
        ('source_platform', sa.Column('source_platform', sa.String(length=20), nullable=True)),
        ('last_commit_at', sa.Column('last_commit_at', sa.DateTime(), nullable=True)),
        ('stars_count', sa.Column('stars_count', sa.Integer(), nullable=True)),
        ('forks_count', sa.Column('forks_count', sa.Integer(), nullable=True)),
        ('watchers_count', sa.Column('watchers_count', sa.Integer(), nullable=True)),
        ('open_issues_count', sa.Column('open_issues_count', sa.Integer(), nullable=True)),
        ('default_branch', sa.Column('default_branch', sa.String(length=255), nullable=True)),
        ('repo_size_kb', sa.Column('repo_size_kb', sa.Integer(), nullable=True)),
    ]
    for name, column in add_specs:
        if name not in project_columns:
            op.add_column('project', column)


def downgrade():
    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.drop_column('repo_size_kb')
        batch_op.drop_column('default_branch')
        batch_op.drop_column('open_issues_count')
        batch_op.drop_column('watchers_count')
        batch_op.drop_column('forks_count')
        batch_op.drop_column('stars_count')
        batch_op.drop_column('last_commit_at')
        batch_op.drop_column('source_platform')
