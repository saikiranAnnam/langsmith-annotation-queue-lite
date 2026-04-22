"""add reservation tracking and span fields

Revision ID: b66454c4a9b1
Revises: 0a3a5ead7ef5
Create Date: 2026-04-22 09:10:16.280660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b66454c4a9b1'
down_revision: Union[str, Sequence[str], None] = '0a3a5ead7ef5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reservation tracking to queue_entries and span fields to feedback."""
    
    # queue_entries: track who reserved an entry and when
    # enables ownership and future stale-lock recovery (TTL)
    op.execute("""
        ALTER TABLE queue_entries
            ADD COLUMN reserved_at TIMESTAMPTZ,
            ADD COLUMN reserved_by VARCHAR(255)
    """)
    
    # feedback: store highlighing metadata for annotations
    # span_path identifies the JSON field, start/end indexes locate text within that field. 
    op.execute("""
        ALTER TABLE feedback
            ADD COLUMN span_path        JSONB,
            ADD COLUMN span_start_index INTEGER,
            ADD COLUMN span_end_index   INTEGER
    """)

# downgrading the changes if needed, i.e. if the changes are not working as expected.
def downgrade() -> None:
    """Remove reservation tracking and span fields from queue_entries and feedback."""
    
    op.execute("""
        ALTER TABLE queue_entries
            DROP COLUMN IF EXISTS reserved_at,
            DROP COLUMN IF EXISTS reserved_by
    """)
    
    op.execute("""
        ALTER TABLE feedback
            DROP COLUMN IF EXISTS span_path,
            DROP COLUMN IF EXISTS span_start_index,
            DROP COLUMN IF EXISTS span_end_index
    """)
