"""Business logic for traces."""

from datetime import datetime
from uuid import UUID

import asyncpg
import orjson

from src.sql_utils import prepare_query


async def create_trace(
    conn: asyncpg.Connection,
    project_id: UUID,
    inputs: dict | None,
    outputs: dict | None,
    trace_metadata: dict | None,
    start_time: datetime,
    end_time: datetime | None,
) -> dict:
    """Create a new trace."""
    # Verify project exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM tracing_projects WHERE id = $project_id)",
        project_id=project_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return None

    query, params = prepare_query(
        """
        INSERT INTO traces (project_id, inputs, outputs, trace_metadata, start_time, end_time)
        VALUES ($project_id, $inputs, $outputs, $trace_metadata, $start_time, $end_time)
        RETURNING id, project_id, inputs, outputs, trace_metadata, start_time, end_time
        """,
        project_id=project_id,
        inputs=orjson.dumps(inputs).decode() if inputs else None,
        outputs=orjson.dumps(outputs).decode() if outputs else None,
        trace_metadata=orjson.dumps(trace_metadata).decode() if trace_metadata else None,
        start_time=start_time,
        end_time=end_time,
    )
    row = await conn.fetchrow(query, *params)
    result = dict(row)

    # Deserialize JSONB fields
    for field in ["inputs", "outputs", "trace_metadata"]:
        if result[field] and isinstance(result[field], str):
            result[field] = orjson.loads(result[field])

    return result


async def query_traces(
    conn: asyncpg.Connection,
    trace_ids: list[UUID] | None = None,
    project_id: UUID | None = None,
    session_id: str | None = None,
) -> list[dict]:
    """Query traces with optional filters."""
    where_clauses = []
    params_dict = {}

    if trace_ids:
        where_clauses.append("id = ANY($trace_ids::uuid[])")
        params_dict["trace_ids"] = trace_ids

    if project_id:
        where_clauses.append("project_id = $project_id")
        params_dict["project_id"] = project_id

    if session_id:
        where_clauses.append("trace_metadata->>'session_id' = $session_id")
        params_dict["session_id"] = session_id

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query_str = f"""
        SELECT id, project_id, inputs, outputs, trace_metadata, start_time, end_time
        FROM traces
        {where_clause}
        ORDER BY start_time DESC
    """

    if params_dict:
        query, params = prepare_query(query_str, **params_dict)
        rows = await conn.fetch(query, *params)
    else:
        rows = await conn.fetch(query_str)

    results = []
    for row in rows:
        result = dict(row)
        for field in ["inputs", "outputs", "trace_metadata"]:
            if result[field] and isinstance(result[field], str):
                result[field] = orjson.loads(result[field])
        results.append(result)

    return results


async def get_trace(conn: asyncpg.Connection, trace_id: UUID) -> dict | None:
    """Get a specific trace by ID."""
    query, params = prepare_query(
        """
        SELECT id, project_id, inputs, outputs, trace_metadata, start_time, end_time
        FROM traces
        WHERE id = $trace_id
        """,
        trace_id=trace_id,
    )
    row = await conn.fetchrow(query, *params)
    if not row:
        return None

    result = dict(row)
    for field in ["inputs", "outputs", "trace_metadata"]:
        if result[field] and isinstance(result[field], str):
            result[field] = orjson.loads(result[field])

    return result


async def delete_trace(conn: asyncpg.Connection, trace_id: UUID) -> bool:
    """Delete a trace. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM traces
        WHERE id = $trace_id
        """,
        trace_id=trace_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"


async def list_trace_feedback(conn: asyncpg.Connection, trace_id: UUID) -> list[dict] | None:
    """List all feedback for a specific trace. Returns None if trace doesn't exist."""
    # Verify trace exists
    query, params = prepare_query(
        "SELECT EXISTS(SELECT 1 FROM traces WHERE id = $trace_id)",
        trace_id=trace_id,
    )
    exists = await conn.fetchval(query, *params)
    if not exists:
        return None

    query, params = prepare_query(
        """
        SELECT id, trace_id, key, score, comment, created_at, modified_at
        FROM feedback
        WHERE trace_id = $trace_id
        ORDER BY created_at DESC
        """,
        trace_id=trace_id,
    )
    rows = await conn.fetch(query, *params)
    results = [dict(row) for row in rows]
    return results
