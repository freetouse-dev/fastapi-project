"""add company multi tenancy

Revision ID: e58f2a1b3c4d
Revises: d49e1f0a2d5f
Create Date: 2026-10-20 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'e58f2a1b3c4d'
down_revision: Union[str, Sequence[str], None] = 'd49e1f0a2d5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column(
            'status',
            sa.Enum('ACTIVE', 'SUSPENDED', 'PENDING_APPROVAL', name='companystatus'),
            nullable=False,
            server_default='ACTIVE',
        ),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_companies_id'), 'companies', ['id'], unique=False)
    op.create_index(op.f('ix_companies_slug'), 'companies', ['slug'], unique=True)
    op.create_index(op.f('ix_companies_deleted_at'), 'companies', ['deleted_at'], unique=False)

    # 2. Create company_members table
    op.create_table(
        'company_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'role',
            sa.Enum('COMPANY_OWNER', 'COMPANY_ADMIN', 'MEMBER', 'VIEWER', name='companyrole'),
            nullable=False,
            server_default='MEMBER',
        ),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('invited_by_id', sa.Integer(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'user_id', name='uq_company_user'),
    )
    op.create_index(op.f('ix_company_members_id'), 'company_members', ['id'], unique=False)
    op.create_index(op.f('ix_company_members_company_id'), 'company_members', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_members_user_id'), 'company_members', ['user_id'], unique=False)

    # 3. Create company_creation_requests table
    op.create_table(
        'company_creation_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=False),
        sa.Column('company_slug', sa.String(length=100), nullable=False),
        sa.Column('business_description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('reviewed_by_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_company_creation_requests_id'), 'company_creation_requests', ['id'], unique=False)
    op.create_index(op.f('ix_company_creation_requests_user_id'), 'company_creation_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_company_creation_requests_company_slug'), 'company_creation_requests', ['company_slug'], unique=False)
    op.create_index(op.f('ix_company_creation_requests_status'), 'company_creation_requests', ['status'], unique=False)

    # 4. Create company_invitations table
    op.create_table(
        'company_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column(
            'role',
            sa.Enum('COMPANY_OWNER', 'COMPANY_ADMIN', 'MEMBER', 'VIEWER', name='companyrole'),
            nullable=False,
            server_default='MEMBER',
        ),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('invited_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_company_invitations_id'), 'company_invitations', ['id'], unique=False)
    op.create_index(op.f('ix_company_invitations_company_id'), 'company_invitations', ['company_id'], unique=False)
    op.create_index(op.f('ix_company_invitations_email'), 'company_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_company_invitations_token_hash'), 'company_invitations', ['token_hash'], unique=True)
    op.create_index(op.f('ix_company_invitations_status'), 'company_invitations', ['status'], unique=False)

    # 5. Add company_id to workspaces (nullable initially for backfill)
    op.add_column('workspaces', sa.Column('company_id', sa.Integer(), nullable=True))

    # 6. Data Backfill
    bind = op.get_bind()

    # Query all existing workspaces
    ws_rows = bind.execute(text("SELECT id, name, slug, owner_id FROM workspaces")).fetchall()
    owner_to_company: dict[int, int] = {}

    for ws in ws_rows:
        ws_id, ws_name, ws_slug, owner_id = ws[0], ws[1], ws[2], ws[3]

        if owner_id not in owner_to_company:
            # Create a company for this owner
            company_name = f"{ws_name} Corp"
            company_slug = f"{ws_slug}-corp"

            # Check if slug exists
            existing_slug = bind.execute(
                text("SELECT id FROM companies WHERE slug = :slug"), {"slug": company_slug}
            ).fetchone()
            if existing_slug:
                company_slug = f"{ws_slug}-{owner_id}"

            bind.execute(
                text(
                    """
                    INSERT INTO companies (name, slug, description, status, owner_id, created_by_id, created_at, updated_at)
                    VALUES (:name, :slug, :desc, 'ACTIVE', :owner_id, :owner_id, NOW(), NOW())
                    """
                ),
                {
                    "name": company_name,
                    "slug": company_slug,
                    "desc": f"Company organization for {ws_name}",
                    "owner_id": owner_id,
                },
            )
            # Retrieve newly created company id
            company_row = bind.execute(
                text("SELECT id FROM companies WHERE slug = :slug"), {"slug": company_slug}
            ).fetchone()
            company_id = company_row[0]
            owner_to_company[owner_id] = company_id

            # Add owner as COMPANY_OWNER in company_members
            bind.execute(
                text(
                    """
                    INSERT INTO company_members (company_id, user_id, role, status, joined_at, created_at)
                    VALUES (:cid, :uid, 'COMPANY_OWNER', 'ACTIVE', NOW(), NOW())
                    """
                ),
                {"cid": company_id, "uid": owner_id},
            )
        else:
            company_id = owner_to_company[owner_id]

        # Link workspace to company
        bind.execute(
            text("UPDATE workspaces SET company_id = :cid WHERE id = :wid"),
            {"cid": company_id, "wid": ws_id},
        )

        # Backfill all members of this workspace into company_members
        ws_members = bind.execute(
            text("SELECT user_id, role FROM workspace_members WHERE workspace_id = :wid"),
            {"wid": ws_id},
        ).fetchall()

        for wm in ws_members:
            m_uid, m_role = wm[0], wm[1]
            existing_cm = bind.execute(
                text("SELECT id FROM company_members WHERE company_id = :cid AND user_id = :uid"),
                {"cid": company_id, "uid": m_uid},
            ).fetchone()
            if not existing_cm:
                comp_role = 'COMPANY_ADMIN' if m_role in ('OWNER', 'ADMIN') else 'MEMBER'
                bind.execute(
                    text(
                        """
                        INSERT INTO company_members (company_id, user_id, role, status, joined_at, created_at)
                        VALUES (:cid, :uid, :role, 'ACTIVE', NOW(), NOW())
                        """
                    ),
                    {"cid": company_id, "uid": m_uid, "role": comp_role},
                )

    # If any workspace still has NULL company_id (edge case), assign fallback
    default_co = bind.execute(text("SELECT id FROM companies LIMIT 1")).fetchone()
    if default_co:
        bind.execute(
            text("UPDATE workspaces SET company_id = :cid WHERE company_id IS NULL"),
            {"cid": default_co[0]},
        )

    # 7. Make workspaces.company_id NOT NULL and add foreign key constraint & index
    op.alter_column('workspaces', 'company_id', existing_type=sa.Integer(), nullable=False)
    op.create_index(op.f('ix_workspaces_company_id'), 'workspaces', ['company_id'], unique=False)
    op.create_foreign_key(
        'fk_workspaces_company_id',
        'workspaces',
        'companies',
        ['company_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_workspaces_company_id', 'workspaces', type_='foreignkey')
    op.drop_index(op.f('ix_workspaces_company_id'), table_name='workspaces')
    op.drop_column('workspaces', 'company_id')

    op.drop_index(op.f('ix_company_invitations_status'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_token_hash'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_email'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_company_id'), table_name='company_invitations')
    op.drop_index(op.f('ix_company_invitations_id'), table_name='company_invitations')
    op.drop_table('company_invitations')

    op.drop_index(op.f('ix_company_creation_requests_status'), table_name='company_creation_requests')
    op.drop_index(op.f('ix_company_creation_requests_company_slug'), table_name='company_creation_requests')
    op.drop_index(op.f('ix_company_creation_requests_user_id'), table_name='company_creation_requests')
    op.drop_index(op.f('ix_company_creation_requests_id'), table_name='company_creation_requests')
    op.drop_table('company_creation_requests')

    op.drop_index(op.f('ix_company_members_user_id'), table_name='company_members')
    op.drop_index(op.f('ix_company_members_company_id'), table_name='company_members')
    op.drop_index(op.f('ix_company_members_id'), table_name='company_members')
    op.drop_table('company_members')

    op.drop_index(op.f('ix_companies_deleted_at'), table_name='companies')
    op.drop_index(op.f('ix_companies_slug'), table_name='companies')
    op.drop_index(op.f('ix_companies_id'), table_name='companies')
    op.drop_table('companies')
