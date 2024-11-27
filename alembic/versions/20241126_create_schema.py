"""Create schema

Revision ID: 20241126_create_schema
Revises: 6d25e058d779
Create Date: 2024-11-26 20:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20241126_create_schema'
down_revision = '6d25e058d779'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tables
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_users')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_roles')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='fk_user_roles_role_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_user_roles_user_id'),
        sa.PrimaryKeyConstraint('user_id', 'role_id', name='pk_user_roles')
    )
    
    op.create_table(
        'tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_tokens_user_id'),
        sa.PrimaryKeyConstraint('id', name='pk_tokens')
    )
    op.create_index(op.f('ix_tokens_id'), 'tokens', ['id'], unique=False)
    
    op.create_table(
        'folders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_root', sa.Boolean(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_folders_owner_id'),
        sa.PrimaryKeyConstraint('id', name='pk_folders')
    )
    op.create_index(op.f('ix_folders_id'), 'folders', ['id'], unique=False)
    
    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('bucket', sa.String(length=100), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('is_latest', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='fk_files_owner_id'),
        sa.PrimaryKeyConstraint('id', name='pk_files'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'processed', 'failed')", name='ck_files_status')
    )
    op.create_index(op.f('ix_files_id'), 'files', ['id'], unique=False)
    
    # Create AI processor tables
    op.create_table(
        'processing_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('params', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], name='fk_processing_tasks_file_id'),
        sa.PrimaryKeyConstraint('id', name='pk_processing_tasks'),
        sa.CheckConstraint("status IN ('queued', 'processing', 'completed', 'failed')", name='ck_processing_tasks_status')
    )
    op.create_index(op.f('ix_processing_tasks_id'), 'processing_tasks', ['id'], unique=False)

    op.create_table(
        'processing_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('result_type', sa.String(length=50), nullable=False),
        sa.Column('result_data', postgresql.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['processing_tasks.id'], name='fk_processing_results_task_id'),
        sa.PrimaryKeyConstraint('id', name='pk_processing_results'),
        sa.UniqueConstraint('task_id', name='uq_processing_results_task_id')
    )
    op.create_index(op.f('ix_processing_results_id'), 'processing_results', ['id'], unique=False)

    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('folder_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_chat_sessions_user_id'),
        sa.PrimaryKeyConstraint('id', name='pk_chat_sessions')
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender', sa.String(length=10), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], name='fk_chat_messages_session_id'),
        sa.PrimaryKeyConstraint('id', name='pk_chat_messages')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_chat_messages_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_index(op.f('ix_processing_results_id'), table_name='processing_results')
    op.drop_table('processing_results')
    op.drop_index(op.f('ix_processing_tasks_id'), table_name='processing_tasks')
    op.drop_table('processing_tasks')
    op.drop_index(op.f('ix_files_id'), table_name='files')
    op.drop_table('files')
    op.drop_index(op.f('ix_folders_id'), table_name='folders')
    op.drop_table('folders')
    op.drop_index(op.f('ix_tokens_id'), table_name='tokens')
    op.drop_table('tokens')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
