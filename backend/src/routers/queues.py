from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import get_connection
from src.services import queues as queues_service

router = APIRouter(prefix="/queues", tags=["queues"])


@router.post("", response_model=schemas.Queue, status_code=status.HTTP_201_CREATED)
async def create_queue(
    queue: schemas.QueueCreate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    return await queues_service.create_queue(conn, queue.name)


@router.get("", response_model=list[schemas.Queue])
async def list_queues(
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    return await queues_service.list_queues(conn)


@router.get("/{queue_id}", response_model=schemas.Queue)
async def get_queue(
    queue_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    queue = await queues_service.get_queue(conn, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return queue


@router.patch("/{queue_id}", response_model=schemas.Queue)
async def update_queue(
    queue_id: UUID,
    queue_update: schemas.QueueUpdate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    result = await queues_service.update_queue(conn, queue_id, queue_update.name)

    if result is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    if result is False:
        raise HTTPException(status_code=404, detail="Queue not found")

    return result


@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_queue(
    queue_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    deleted = await queues_service.delete_queue(conn, queue_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Queue not found")


@router.post("/{queue_id}/populate", status_code=status.HTTP_201_CREATED)
async def populate_queue(
    queue_id: UUID,
    populate_request: schemas.QueuePopulateRequest,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    """Add traces to a queue."""
    success, missing_trace_ids = await queues_service.populate_queue(conn, queue_id, populate_request.trace_ids)

    if not success and missing_trace_ids is None:
        raise HTTPException(status_code=404, detail="Queue not found")

    if not success and missing_trace_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Traces not found: {sorted(missing_trace_ids)}",
        )

    return {"message": f"Added {len(populate_request.trace_ids)} entries to queue"}


@router.get("/{queue_id}/entries/next", response_model=schemas.QueueEntry)
async def get_next_entry(
    queue_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    """Get the next pending entry from the queue."""
    result = await queues_service.get_next_entry(conn, queue_id)

    if result is False:
        raise HTTPException(status_code=404, detail="Queue not found")

    if result is None:
        raise HTTPException(status_code=404, detail="No pending entries in queue")

    return result


@router.post("/{queue_id}/entries/{entry_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_entry(
    queue_id: UUID,
    entry_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    """Mark an entry as complete and remove it from the queue."""
    success, message = await queues_service.complete_entry(conn, queue_id, entry_id)

    if not success:
        if message == "queue_not_found":
            raise HTTPException(status_code=404, detail="Queue not found")
        elif message == "entry_not_found":
            raise HTTPException(status_code=404, detail="Queue entry not found")


@router.post("/{queue_id}/entries/{entry_id}/requeue", status_code=status.HTTP_200_OK)
async def requeue_entry(
    queue_id: UUID,
    entry_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    """Re-queue an entry (reset status to pending and update timestamp)."""
    success, message = await queues_service.requeue_entry(conn, queue_id, entry_id)

    if not success:
        if message == "queue_not_found":
            raise HTTPException(status_code=404, detail="Queue not found")
        elif message == "entry_not_found":
            raise HTTPException(status_code=404, detail="Queue entry not found")

    return {"message": "Entry re-queued successfully"}
