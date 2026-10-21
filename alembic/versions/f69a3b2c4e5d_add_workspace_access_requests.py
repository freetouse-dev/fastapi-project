"""add workspace access requests and member permission

Revision ID: f69a3b2c4e5d
Revises: e58f2a1b3c4d
Create Date: 2026-10-20 20:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'f69a3b2c4e5d'
down_revision: Union[str, Sequence[str], None] = 'e58f2a1b3c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add can_create_workspace to company_members
    op.add_column(
        'company_members',
        sa.Column('can_create_workspace', sa.Boolean(), nullable=False, server_default=sa.false())
    )

    # 2. Backfill existing COMPANY_OWNER and COMPANY_ADMIN members with can_create_workspace = TRUE
    op.execute(text("UPDATE company_members SET can_create_workspace = TRUE WHERE role IN ('COMPANY_OWNER', 'COMPANY_ADMIN')"))

    # 3. Create workspace_access_requests table
    op.create_table(
        'workspace_access_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'request_type',
            sa.Enum('CREATE_WORKSPACE', 'JOIN_WORKSPACE', name='workspaceaccessrequesttype'),
            nullable=False,
            server_default='CREATE_WORKSPACE',
        ),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('requested_role', sa.String(length=50), nullable=True),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED', name='workspaceaccessrequeststatus'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workspace_access_requests_id'), 'workspace_access_requests', ['id'], unique=False)
    op.create_index(op.f('ix_workspace_access_requests_company_id'), 'workspace_access_requests', ['company_id'], unique=False)
    op.create_index(op.f('ix_workspace_access_requests_user_id'), 'workspace_access_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_workspace_access_requests_workspace_id'), 'workspace_access_requests', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_workspace_access_requests_status'), 'workspace_access_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_workspace_access_requests_status'), table_name='workspace_access_requests')
    op.drop_index(op.f('ix_workspace_access_requests_workspace_id'), table_name='workspace_access_requests')
    op.drop_index(op.f('ix_workspace_access_requests_user_id'), table_name='workspace_access_requests')
    op.drop_index(op.f('ix_workspace_access_requests_company_id'), table_name='workspace_access_requests')
    op.drop_index(op.f('ix_workspace_access_requests_id'), table_name='workspace_access_requests')
    op.drop_table('workspace_access_requests')
    op.drop_column('company_members', 'can_create_workspace')
