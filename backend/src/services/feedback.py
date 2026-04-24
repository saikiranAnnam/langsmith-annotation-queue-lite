"""Business logic for feedback."""

import json
from uuid import UUID

import asyncpg

from src import schemas
from src.sql_utils import prepare_query


def _parse_row(row: asyncpg.Record) -> dict:
    """Convert an asyncpg row to a dict, deserializing span_path from its JSON string."""
    d = dict(row)
    if isinstance(d.get("span_path"), str):
        d["span_path"] = json.loads(d["span_path"])
    return d


async def create_feedback_batch(
    conn: asyncpg.Connection,
    feedback_batch: list[schemas.FeedbackCreate],
) -> list[dict]:
    """Upsert a batch of feedback records — first submit creates, re-score updates. Idempotent on (trace_id, key)."""
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

    # Build insert tuples — span fields are optional, None when not provided
    insert_values = []
    for feedback in feedback_batch:
        insert_values.append(
            (
                feedback.trace_id,
                feedback.key,
                feedback.score,
                feedback.comment,
                json.dumps(feedback.span_path) if feedback.span_path else None,
                feedback.span_start_index,
                feedback.span_end_index,
            )
        )

    # Upsert — ON CONFLICT updates the existing row so duplicate (trace_id, key)
    # pairs are never created, regardless of what client is calling this endpoint.
    rows = await conn.fetch(
        """
        INSERT INTO feedback (trace_id, key, score, comment, span_path, span_start_index, span_end_index)
        SELECT * FROM UNNEST($1::uuid[], $2::text[], $3::float[], $4::text[], $5::jsonb[], $6::int[], $7::int[])
        ON CONFLICT (trace_id, key) DO UPDATE SET
            score             = EXCLUDED.score,
            comment           = EXCLUDED.comment,
            span_path         = EXCLUDED.span_path,
            span_start_index  = EXCLUDED.span_start_index,
            span_end_index    = EXCLUDED.span_end_index,
            modified_at       = NOW()
        RETURNING id, trace_id, key, score, comment, span_path, span_start_index, span_end_index, created_at, modified_at
        """,
        [v[0] for v in insert_values],  # trace_ids
        [v[1] for v in insert_values],  # keys
        [v[2] for v in insert_values],  # scores
        [v[3] for v in insert_values],  # comments
        [v[4] for v in insert_values],  # span_paths
        [v[5] for v in insert_values],  # span_start_indices
        [v[6] for v in insert_values],  # span_end_indices
    )

    return [_parse_row(row) for row in rows]

async def get_feedback(conn: asyncpg.Connection, feedback_id: UUID) -> dict | None:
    """Fetch a single feedback record by id, including any span selection metadata."""
    query, params = prepare_query(
        """
        SELECT id, trace_id, key, score, comment,
               span_path, span_start_index, span_end_index,
               created_at, modified_at
        FROM feedback
        WHERE id = $feedback_id
        """,
        feedback_id=feedback_id,
    )
    row = await conn.fetchrow(query, *params)
    return _parse_row(row) if row else None


async def update_feedback(
    conn: asyncpg.Connection,
    feedback_id: UUID,
    feedback_update: schemas.FeedbackUpdate,
) -> dict | None:
    """Partially update a feedback record. Only provided fields are written."""
    updates = {}

    if feedback_update.score is not None:
        updates["score"] = feedback_update.score

    if feedback_update.comment is not None:
        updates["comment"] = feedback_update.comment

    if feedback_update.span_path is not None:
        # asyncpg expects jsonb as a serialized string for named-param queries
        updates["span_path"] = json.dumps(feedback_update.span_path)

    if feedback_update.span_start_index is not None:
        updates["span_start_index"] = feedback_update.span_start_index

    if feedback_update.span_end_index is not None:
        updates["span_end_index"] = feedback_update.span_end_index

    if not updates:
        return None  # Signal no fields to update

    set_clauses = [f"{field} = ${field}" for field in updates.keys()]
    set_clauses.append("modified_at = NOW()")

    query_str = f"""
        UPDATE feedback
        SET {", ".join(set_clauses)}
        WHERE id = $feedback_id
        RETURNING id, trace_id, key, score, comment,
                  span_path, span_start_index, span_end_index,
                  created_at, modified_at
    """

    params_dict = dict(updates)
    params_dict["feedback_id"] = feedback_id

    query, params = prepare_query(query_str, **params_dict)
    row = await conn.fetchrow(query, *params)
    if not row:
        return False  # Signal not found

    return _parse_row(row)


async def delete_feedback(conn: asyncpg.Connection, feedback_id: UUID) -> bool:
    """Delete a feedback record. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM feedback
        WHERE id = $feedback_id
        """,
        feedback_id=feedback_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"
