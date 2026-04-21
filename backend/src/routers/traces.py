from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import get_connection
from src.services import traces as traces_service

router = APIRouter(prefix="/traces", tags=["traces"])


@router.post("", response_model=schemas.Trace, status_code=status.HTTP_201_CREATED)
async def create_trace(
    trace: schemas.TraceCreate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    result = await traces_service.create_trace(
        conn,
        trace.project_id,
        trace.inputs,
        trace.outputs,
        trace.trace_metadata,
        trace.start_time,
        trace.end_time,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Project not found")
    return result


@router.post("/query", response_model=list[schemas.Trace])
async def query_traces(
    query_request: schemas.TraceQueryRequest,
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    """Query traces with optional filters."""
    return await traces_service.query_traces(
        conn,
        trace_ids=query_request.trace_ids,
        project_id=query_request.project_id,
        session_id=query_request.session_id,
    )


@router.get("/{trace_id}", response_model=schemas.Trace)
async def get_trace(
    trace_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    trace = await traces_service.get_trace(conn, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace


@router.get("/{trace_id}/feedback", response_model=list[schemas.Feedback])
async def list_trace_feedback(
    trace_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    """List all feedback for a specific trace."""
    feedback = await traces_service.list_trace_feedback(conn, trace_id)
    if feedback is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return feedback


@router.delete("/{trace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace(
    trace_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    deleted = await traces_service.delete_trace(conn, trace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trace not found")
