"""add retry fields

Revision ID: 20240101_add_retry_fields
Revises: previous_revision
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240101_add_retry_fields'
down_revision = 'previous_revision'  # Update this to your previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add retry_count field
    op.add_column('processing_tasks', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    
    # Add last_retry_at field
    op.add_column('processing_tasks', sa.Column('last_retry_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add batch_id field
    op.add_column('processing_tasks', sa.Column('batch_id', sa.String(50), nullable=True))
    op.create_index(op.f('ix_processing_tasks_batch_id'), 'processing_tasks', ['batch_id'])
    
    # Update status enum
    op.execute("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'retrying' AFTER 'failed'")
    
    # Update confidence_score type in results
    op.alter_column('processing_results', 'confidence_score',
                    existing_type=sa.Integer(),
                    type_=sa.Float(),
                    existing_nullable=True)

def downgrade() -> None:
    # Cannot remove enum value, so skip that in downgrade
    
    # Remove indexes
    op.drop_index(op.f('ix_processing_tasks_batch_id'), 'processing_tasks')
    
    # Remove columns
    op.drop_column('processing_tasks', 'batch_id')
    op.drop_column('processing_tasks', 'last_retry_at')
    op.drop_column('processing_tasks', 'retry_count')
    
    # Revert confidence_score type
    op.alter_column('processing_results', 'confidence_score',
                    existing_type=sa.Float(),
                    type_=sa.Integer(),
                    existing_nullable=True)
