"""Business logic for feedback."""

from uuid import UUID

import asyncpg

from src import schemas
from src.sql_utils import prepare_query


async def create_feedback_batch(
    conn: asyncpg.Connection,
    feedback_batch: list[schemas.FeedbackCreate],
) -> list[dict]:
    """Create multiple feedback items at once."""
    if not feedback_batch:
        return None  # Signal empty batch error

    # Validate all trace_ids exist
    trace_ids = {fb.trace_id for fb in feedback_batch}
    query, params = prepare_query(
        """
        SELECT id FROM traces
        WHERE id = ANY($trace_ids::uuid[])
        """,
        trace_ids=list(trace_ids),
    )
    traces = await conn.fetch(query, *params)
    found_trace_ids = {row["id"] for row in traces}
    missing_trace_ids = trace_ids - found_trace_ids
    if missing_trace_ids:
        return None, missing_trace_ids  # Signal missing traces

    # Prepare batch insert data
    insert_values = []
    for feedback in feedback_batch:
        insert_values.append(
            (
                feedback.trace_id,
                feedback.key,
                feedback.score,
                feedback.comment,
            )
        )

    # Insert all feedback items in batch
    rows = await conn.fetch(
        """
        INSERT INTO feedback (trace_id, key, score, comment)
        SELECT * FROM UNNEST($1::uuid[], $2::text[], $3::float[], $4::text[])
        RETURNING id, trace_id, key, score, comment, created_at, modified_at
        """,
        [v[0] for v in insert_values],  # trace_ids
        [v[1] for v in insert_values],  # keys
        [v[2] for v in insert_values],  # scores
        [v[3] for v in insert_values],  # comments
    )

    # Process results
    results = [dict(row) for row in rows]
    return results


async def update_feedback(
    conn: asyncpg.Connection,
    feedback_id: UUID,
    feedback_update: schemas.FeedbackUpdate,
) -> dict | None:
    """Update a feedback item."""
    # Build dynamic update query with named params
    updates = {}

    if feedback_update.score is not None:
        updates["score"] = feedback_update.score

    if feedback_update.comment is not None:
        updates["comment"] = feedback_update.comment

    if not updates:
        return None  # Signal no fields to update

    # Build SET clause with named parameters
    set_clauses = []
    for field in updates.keys():
        set_clauses.append(f"{field} = ${field}")
    set_clauses.append("modified_at = NOW()")

    query_str = f"""
        UPDATE feedback
        SET {", ".join(set_clauses)}
        WHERE id = $feedback_id
        RETURNING id, trace_id, key, score, comment, created_at, modified_at
    """

    # Remove modified_at from params since we handle it with NOW()
    params_dict = dict(updates)
    params_dict["feedback_id"] = feedback_id

    query, params = prepare_query(query_str, **params_dict)
    row = await conn.fetchrow(query, *params)
    if not row:
        return False  # Signal not found

    result = dict(row)
    return result


async def delete_feedback(conn: asyncpg.Connection, feedback_id: UUID) -> bool:
    """Delete a feedback item. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM feedback
        WHERE id = $feedback_id
        """,
        feedback_id=feedback_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"
