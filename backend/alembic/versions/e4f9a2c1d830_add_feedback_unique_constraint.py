"""add unique constraint on feedback (trace_id, key)

Revision ID: e4f9a2c1d830
Revises: b66454c4a9b1
Create Date: 2026-04-24 12:00:00.000000

Makes the backend authoritative on feedback uniqueness per trace+key.
Before this, duplicate rows were prevented only by frontend logic — any
direct API call or second client could create duplicates. The batch insert
now uses ON CONFLICT DO UPDATE (upsert), so the constraint is enforced
at the DB level regardless of the caller.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e4f9a2c1d830'
down_revision: Union[str, Sequence[str], None] = 'b66454c4a9b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove any duplicate (trace_id, key) rows that may exist before adding
    # the constraint — keeps the most recently modified row for each pair.
    op.execute("""
        DELETE FROM feedback
        WHERE id NOT IN (
            SELECT DISTINCT ON (trace_id, key) id
            FROM feedback
            ORDER BY trace_id, key, modified_at DESC
        )
    """)

    op.execute("""
        ALTER TABLE feedback
            ADD CONSTRAINT feedback_trace_key_unique UNIQUE (trace_id, key)
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE feedback
            DROP CONSTRAINT IF EXISTS feedback_trace_key_unique
    """)
