"""Business logic for queues and queue operations."""

from uuid import UUID

import asyncpg
import orjson

from src.sql_utils import prepare_query


async def create_queue(conn: asyncpg.Connection, name: str) -> dict:
    """Create a new queue."""
    query, params = prepare_query(
        """
        INSERT INTO queues (name)
        VALUES ($name)
        RETURNING id, name, created_at, modified_at
        """,
        name=name,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row)


async def list_queues(conn: asyncpg.Connection) -> list[dict]:
    """List all queues with pending entry counts."""
    rows = await conn.fetch(
        """
        SELECT q.id, q.name, q.created_at, q.modified_at,
               COUNT(qe.id) FILTER (WHERE qe.status = 'pending') AS pending_count
        FROM queues q
        LEFT JOIN queue_entries qe ON qe.queue_id = q.id
        GROUP BY q.id, q.name, q.created_at, q.modified_at
        ORDER BY q.created_at DESC
        """
    )
    return [dict(row) for row in rows]


async def get_queue(conn: asyncpg.Connection, queue_id: UUID) -> dict | None:
    """Get a specific queue by ID with pending entry count."""
    query, params = prepare_query(
        """
        SELECT q.id, q.name, q.created_at, q.modified_at,
               COUNT(qe.id) FILTER (WHERE qe.status = 'pending') AS pending_count
        FROM queues q
        LEFT JOIN queue_entries qe ON qe.queue_id = q.id
        WHERE q.id = $queue_id
        GROUP BY q.id, q.name, q.created_at, q.modified_at
        """,
        queue_id=queue_id,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else None


async def update_queue(conn: asyncpg.Connection, queue_id: UUID, name: str | None) -> dict | None:
    """Update a queue."""
    if name is None:
        return None  # Signal no fields to update

    query, params = prepare_query(
        """
        UPDATE queues
        SET name = $name, modified_at = NOW()
        WHERE id = $queue_id
        RETURNING id, name, created_at, modified_at
        """,
        name=name,
        queue_id=queue_id,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else False  # False signals not found


async def delete_queue(conn: asyncpg.Connection, queue_id: UUID) -> bool:
    """Delete a queue. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM queues
        WHERE id = $queue_id
        """,
        queue_id=queue_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"


async def populate_queue(
    conn: asyncpg.Connection, queue_id: UUID, trace_ids: list[UUID]
) -> tuple[bool, list[UUID] | None]:
    """
    Populate a queue with traces.
    Returns (success, missing_trace_ids).
    - (True, None) if successful
    - (False, None) if queue not found
    - (False, [missing_ids]) if some traces not found
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return False, None

    # Verify all traces exist
    query, params = prepare_query(
        "SELECT id FROM traces WHERE id = ANY($trace_ids::uuid[])",
        trace_ids=trace_ids,
    )
    rows = await conn.fetch(query, *params)
    found_trace_ids = {row["id"] for row in rows}
    missing_trace_ids = [tid for tid in trace_ids if tid not in found_trace_ids]

    if missing_trace_ids:
        return False, missing_trace_ids

    # Insert queue entries in batch using executemany
    await conn.executemany(
        """
        INSERT INTO queue_entries (queue_id, trace_id, status)
        VALUES ($1, $2, 'pending')
        """,
        [(queue_id, trace_id) for trace_id in trace_ids],
    )

    return True, None


async def get_next_entry(conn: asyncpg.Connection, queue_id: UUID) -> dict | None:
    """
    Get the next pending entry from a queue.
    Returns None if queue is empty or queue doesn't exist.
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return False  # Signal queue not found

    # Get the next pending entry
    query, params = prepare_query(
        """
        SELECT qe.id, qe.trace_id, qe.queue_id, qe.status, qe.added_at,
               t.id as trace_id, t.project_id, t.inputs, t.outputs,
               t.trace_metadata, t.start_time, t.end_time
        FROM queue_entries qe
        JOIN traces t ON t.id = qe.trace_id
        WHERE qe.queue_id = $queue_id AND qe.status = 'pending'
        ORDER BY qe.added_at
        LIMIT 1
        """,
        queue_id=queue_id,
    )
    row = await conn.fetchrow(query, *params)

    if not row:
        return None  # Signal empty queue

    # Build result with trace data
    result = dict(row)
    trace_data = {
        "id": result["trace_id"],
        "project_id": result["project_id"],
        "inputs": result["inputs"],
        "outputs": result["outputs"],
        "trace_metadata": result["trace_metadata"],
        "start_time": result["start_time"],
        "end_time": result["end_time"],
    }

    # Convert JSON strings to dicts
    for field in ["inputs", "outputs", "trace_metadata"]:
        if trace_data[field] and isinstance(trace_data[field], str):
            trace_data[field] = orjson.loads(trace_data[field])

    return {
        "id": result["id"],
        "trace_id": result["trace_id"],
        "queue_id": result["queue_id"],
        "status": result["status"],
        "added_at": result["added_at"],
        "trace": trace_data,
    }


async def complete_entry(conn: asyncpg.Connection, queue_id: UUID, entry_id: UUID) -> tuple[bool, str]:
    """
    Complete and delete a queue entry.
    Returns (success, message).
    - (True, "") if successful
    - (False, "queue_not_found") if queue doesn't exist
    - (False, "entry_not_found") if entry doesn't exist or doesn't belong to queue
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return False, "queue_not_found"

    # Delete the entry
    query, params = prepare_query(
        """
        DELETE FROM queue_entries
        WHERE id = $entry_id AND queue_id = $queue_id
        """,
        entry_id=entry_id,
        queue_id=queue_id,
    )
    result = await conn.execute(query, *params)

    if result == "DELETE 0":
        return False, "entry_not_found"

    return True, ""


async def requeue_entry(conn: asyncpg.Connection, queue_id: UUID, entry_id: UUID) -> tuple[bool, str]:
    """
    Requeue an entry (reset status to pending and update timestamp).
    Returns (success, message).
    - (True, "") if successful
    - (False, "queue_not_found") if queue doesn't exist
    - (False, "entry_not_found") if entry doesn't exist or doesn't belong to queue
    """
    # Verify queue exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM queues WHERE id = $queue_id)",
        queue_id=queue_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return False, "queue_not_found"

    # Update entry to reset status and timestamp
    query, params = prepare_query(
        """
        UPDATE queue_entries
        SET status = 'pending', added_at = NOW()
        WHERE id = $entry_id AND queue_id = $queue_id
        """,
        entry_id=entry_id,
        queue_id=queue_id,
    )
    result = await conn.execute(query, *params)

    if result == "UPDATE 0":
        return False, "entry_not_found"

    return True, ""
