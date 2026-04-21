"""Initial schema

Revision ID: 0a3a5ead7ef5
Revises:
Create Date: 2025-11-26 11:19:26.339328

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0a3a5ead7ef5"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable uuid-ossp extension for UUID generation
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create tracing_projects table
    op.execute("""
        CREATE TABLE tracing_projects (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Create traces table
    op.execute("""
        CREATE TABLE traces (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            project_id UUID NOT NULL REFERENCES tracing_projects(id) ON DELETE CASCADE,
            inputs JSONB,
            outputs JSONB,
            trace_metadata JSONB,
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ix_traces_project_id ON traces(project_id)")

    # Create queues table
    op.execute("""
        CREATE TABLE queues (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Create queue_rubric_items table
    op.execute("""
        CREATE TABLE queue_rubric_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            queue_id UUID NOT NULL REFERENCES queues(id) ON DELETE CASCADE,
            feedback_key VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            CONSTRAINT uq_queue_feedback_key UNIQUE (queue_id, feedback_key)
        )
    """)
    op.execute("CREATE INDEX ix_queue_rubric_items_queue_id ON queue_rubric_items(queue_id)")

    # Create queue_entries table
    op.execute("""
        CREATE TABLE queue_entries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            trace_id UUID NOT NULL REFERENCES traces(id) ON DELETE CASCADE,
            queue_id UUID NOT NULL REFERENCES queues(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ix_queue_entries_queue_id_status_added_at ON queue_entries(queue_id, status, added_at)")
    op.execute("CREATE INDEX ix_queue_entries_trace_id ON queue_entries(trace_id)")

    # Create feedback table
    op.execute("""
        CREATE TABLE feedback (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            trace_id UUID NOT NULL REFERENCES traces(id) ON DELETE CASCADE,
            key VARCHAR(255) NOT NULL,
            score FLOAT,
            comment TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            modified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX ix_feedback_trace_id ON feedback(trace_id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS feedback CASCADE")
    op.execute("DROP TABLE IF EXISTS queue_entries CASCADE")
    op.execute("DROP TABLE IF EXISTS queue_rubric_items CASCADE")
    op.execute("DROP TABLE IF EXISTS queues CASCADE")
    op.execute("DROP TABLE IF EXISTS traces CASCADE")
    op.execute("DROP TABLE IF EXISTS tracing_projects CASCADE")
