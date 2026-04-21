from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import get_connection
from src.services import feedback as feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/batch", response_model=list[schemas.Feedback], status_code=status.HTTP_201_CREATED)
async def create_feedback_batch(
    feedback_batch: list[schemas.FeedbackCreate],
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    """Create multiple feedback items at once."""
    result = await feedback_service.create_feedback_batch(conn, feedback_batch)

    if result is None:
        raise HTTPException(status_code=400, detail="Feedback batch cannot be empty")

    if isinstance(result, tuple):
        # Unpack missing trace IDs
        _, missing_trace_ids = result
        raise HTTPException(
            status_code=404,
            detail=f"Traces not found: {sorted(missing_trace_ids)}",
        )

    return result


@router.patch("/{feedback_id}", response_model=schemas.Feedback)
async def update_feedback(
    feedback_id: UUID,
    feedback_update: schemas.FeedbackUpdate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    result = await feedback_service.update_feedback(conn, feedback_id, feedback_update)

    if result is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    if result is False:
        raise HTTPException(status_code=404, detail="Feedback not found")

    return result


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    deleted = await feedback_service.delete_feedback(conn, feedback_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Feedback not found")
