from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import get_connection
from src.services import rubrics as rubrics_service

router = APIRouter(prefix="/queues/{queue_id}/rubric", tags=["rubrics"])


@router.post("", response_model=schemas.QueueRubricItem, status_code=status.HTTP_201_CREATED)
async def create_rubric_item(
    queue_id: UUID,
    rubric_item: schemas.QueueRubricItemCreate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    result = await rubrics_service.create_rubric_item(
        conn,
        queue_id,
        rubric_item.feedback_key,
        rubric_item.description,
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Queue not found")

    if result is False:
        raise HTTPException(
            status_code=400,
            detail=f"Rubric item with feedback_key '{rubric_item.feedback_key}' already exists for this queue",
        )

    return result


@router.get("", response_model=list[schemas.QueueRubricItem])
async def list_rubric_items(
    queue_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    result = await rubrics_service.list_rubric_items(conn, queue_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Queue not found")

    return result


@router.get("/{rubric_item_id}", response_model=schemas.QueueRubricItem)
async def get_rubric_item(
    queue_id: UUID,
    rubric_item_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    rubric_item = await rubrics_service.get_rubric_item(conn, queue_id, rubric_item_id)

    if not rubric_item:
        raise HTTPException(status_code=404, detail="Rubric item not found")

    return rubric_item


@router.patch("/{rubric_item_id}", response_model=schemas.QueueRubricItem)
async def update_rubric_item(
    queue_id: UUID,
    rubric_item_id: UUID,
    rubric_item_update: schemas.QueueRubricItemUpdate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    result = await rubrics_service.update_rubric_item(
        conn,
        queue_id,
        rubric_item_id,
        rubric_item_update.description,
    )

    if result is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    if result is False:
        raise HTTPException(status_code=404, detail="Rubric item not found")

    return result


@router.delete("/{rubric_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rubric_item(
    queue_id: UUID,
    rubric_item_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    deleted = await rubrics_service.delete_rubric_item(conn, queue_id, rubric_item_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Rubric item not found")
