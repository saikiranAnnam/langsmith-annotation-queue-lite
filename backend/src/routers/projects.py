from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from src import schemas
from src.database import get_connection
from src.services import projects as projects_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=schemas.TracingProject, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: schemas.TracingProjectCreate,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    return await projects_service.create_project(conn, project.name)


@router.get("", response_model=list[schemas.TracingProject])
async def list_projects(
    conn: asyncpg.Connection = Depends(get_connection),
) -> list[dict]:
    return await projects_service.list_projects(conn)


@router.get("/{project_id}", response_model=schemas.TracingProject)
async def get_project(
    project_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> dict:
    project = await projects_service.get_project(conn, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    conn: asyncpg.Connection = Depends(get_connection),
) -> None:
    deleted = await projects_service.delete_project(conn, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
