"""Business logic for queue rubric items."""

from uuid import UUID

import asyncpg

from src.sql_utils import prepare_query


async def create_rubric_item(
    conn: asyncpg.Connection,
    queue_id: UUID,
    feedback_key: str,
    description: str,
) -> dict | None:
    """
    Create a rubric item for a queue.
    Returns the created item or None if queue doesn't exist or unique constraint violated.
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return None

    try:
        query, params = prepare_query(
            """
            INSERT INTO queue_rubric_items (queue_id, feedback_key, description)
            VALUES ($queue_id, $feedback_key, $description)
            RETURNING id, queue_id, feedback_key, description
            """,
            queue_id=queue_id,
            feedback_key=feedback_key,
            description=description,
        )
        row = await conn.fetchrow(query, *params)
        return dict(row)
    except asyncpg.UniqueViolationError:
        return False  # Signal duplicate


async def list_rubric_items(conn: asyncpg.Connection, queue_id: UUID) -> list[dict] | None:
    """
    List all rubric items for a queue.
    Returns None if queue doesn't exist.
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return None

    query, params = prepare_query(
        """
        SELECT id, queue_id, feedback_key, description
        FROM queue_rubric_items
        WHERE queue_id = $queue_id
        ORDER BY feedback_key
        """,
        queue_id=queue_id,
    )
    rows = await conn.fetch(query, *params)
    return [dict(row) for row in rows]


async def get_rubric_item(conn: asyncpg.Connection, queue_id: UUID, rubric_item_id: UUID) -> dict | None:
    """Get a specific rubric item by ID."""
    query, params = prepare_query(
        """
        SELECT id, queue_id, feedback_key, description
        FROM queue_rubric_items
        WHERE id = $rubric_item_id AND queue_id = $queue_id
        """,
        rubric_item_id=rubric_item_id,
        queue_id=queue_id,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else None


async def update_rubric_item(
    conn: asyncpg.Connection,
    queue_id: UUID,
    rubric_item_id: UUID,
    description: str | None,
) -> dict | None:
    """Update a rubric item. Returns None if no fields to update, False if not found."""
    if description is None:
        return None  # Signal no fields to update

    query, params = prepare_query(
        """
        UPDATE queue_rubric_items
        SET description = $description
        WHERE id = $rubric_item_id AND queue_id = $queue_id
        RETURNING id, queue_id, feedback_key, description
        """,
        description=description,
        rubric_item_id=rubric_item_id,
        queue_id=queue_id,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else False  # False signals not found


async def delete_rubric_item(conn: asyncpg.Connection, queue_id: UUID, rubric_item_id: UUID) -> bool:
    """Delete a rubric item. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM queue_rubric_items
        WHERE id = $rubric_item_id AND queue_id = $queue_id
        """,
        rubric_item_id=rubric_item_id,
        queue_id=queue_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"
