"""add soft delete and audit logs

Revision ID: c83e1f0a2d5e
Revises: 070f62f02a7b
Create Date: 2026-10-20 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c83e1f0a2d5e'
down_revision: Union[str, Sequence[str], None] = '070f62f02a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add soft-delete fields to workspaces
    op.add_column('workspaces', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('workspaces', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_workspaces_deleted_at'), 'workspaces', ['deleted_at'], unique=False)
    op.create_foreign_key('fk_workspaces_deleted_by', 'workspaces', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')

    # 2. Add soft-delete fields to projects
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('projects', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_projects_deleted_at'), 'projects', ['deleted_at'], unique=False)
    op.create_foreign_key('fk_projects_deleted_by', 'projects', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')

    # 3. Add soft-delete fields to tasks
    op.add_column('tasks', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_tasks_deleted_at'), 'tasks', ['deleted_at'], unique=False)
    op.create_foreign_key('fk_tasks_deleted_by', 'tasks', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')

    # 4. Add soft-delete fields to task_comments
    op.add_column('task_comments', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('task_comments', sa.Column('deleted_by_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_task_comments_deleted_at'), 'task_comments', ['deleted_at'], unique=False)
    op.create_foreign_key('fk_task_comments_deleted_by', 'task_comments', 'users', ['deleted_by_id'], ['id'], ondelete='SET NULL')

    # 5. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')

    op.drop_constraint('fk_task_comments_deleted_by', 'task_comments', type_='foreignkey')
    op.drop_index(op.f('ix_task_comments_deleted_at'), table_name='task_comments')
    op.drop_column('task_comments', 'deleted_by_id')
    op.drop_column('task_comments', 'deleted_at')

    op.drop_constraint('fk_tasks_deleted_by', 'tasks', type_='foreignkey')
    op.drop_index(op.f('ix_tasks_deleted_at'), table_name='tasks')
    op.drop_column('tasks', 'deleted_by_id')
    op.drop_column('tasks', 'deleted_at')

    op.drop_constraint('fk_projects_deleted_by', 'projects', type_='foreignkey')
    op.drop_index(op.f('ix_projects_deleted_at'), table_name='projects')
    op.drop_column('projects', 'deleted_by_id')
    op.drop_column('projects', 'deleted_at')

    op.drop_constraint('fk_workspaces_deleted_by', 'workspaces', type_='foreignkey')
    op.drop_index(op.f('ix_workspaces_deleted_at'), table_name='workspaces')
    op.drop_column('workspaces', 'deleted_by_id')
    op.drop_column('workspaces', 'deleted_at')
