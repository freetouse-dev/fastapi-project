"""add avatar and comment attachments

Revision ID: d49e1f0a2d5f
Revises: c83e1f0a2d5e
Create Date: 2026-10-20 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd49e1f0a2d5f'
down_revision: Union[str, Sequence[str], None] = 'c83e1f0a2d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add avatar_storage_key to users
    op.add_column('users', sa.Column('avatar_storage_key', sa.String(length=255), nullable=True))

    # 2. Create comment_attachments table
    op.create_table(
        'comment_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['task_comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['deleted_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_comment_attachments_id'), 'comment_attachments', ['id'], unique=False)
    op.create_index(op.f('ix_comment_attachments_comment_id'), 'comment_attachments', ['comment_id'], unique=False)
    op.create_index(op.f('ix_comment_attachments_storage_key'), 'comment_attachments', ['storage_key'], unique=True)
    op.create_index(op.f('ix_comment_attachments_uploaded_by_id'), 'comment_attachments', ['uploaded_by_id'], unique=False)
    op.create_index(op.f('ix_comment_attachments_deleted_at'), 'comment_attachments', ['deleted_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_comment_attachments_deleted_at'), table_name='comment_attachments')
    op.drop_index(op.f('ix_comment_attachments_uploaded_by_id'), table_name='comment_attachments')
    op.drop_index(op.f('ix_comment_attachments_storage_key'), table_name='comment_attachments')
    op.drop_index(op.f('ix_comment_attachments_comment_id'), table_name='comment_attachments')
    op.drop_index(op.f('ix_comment_attachments_id'), table_name='comment_attachments')
    op.drop_table('comment_attachments')

    op.drop_column('users', 'avatar_storage_key')
