"""Business logic for tracing projects."""

from uuid import UUID

import asyncpg

from src.sql_utils import prepare_query


async def create_project(conn: asyncpg.Connection, name: str) -> dict:
    """Create a new tracing project."""
    query, params = prepare_query(
        """
        INSERT INTO tracing_projects (name)
        VALUES ($name)
        RETURNING id, name, created_at, modified_at
        """,
        name=name,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row)


async def list_projects(conn: asyncpg.Connection) -> list[dict]:
    """List all tracing projects."""
    rows = await conn.fetch(
        """
        SELECT id, name, created_at, modified_at
        FROM tracing_projects
        ORDER BY created_at DESC
        """
    )
    return [dict(row) for row in rows]


async def get_project(conn: asyncpg.Connection, project_id: UUID) -> dict | None:
    """Get a specific tracing project by ID."""
    query, params = prepare_query(
        """
        SELECT id, name, created_at, modified_at
        FROM tracing_projects
        WHERE id = $project_id
        """,
        project_id=project_id,
    )
    row = await conn.fetchrow(query, *params)
    return dict(row) if row else None


async def delete_project(conn: asyncpg.Connection, project_id: UUID) -> bool:
    """Delete a tracing project. Returns True if deleted, False if not found."""
    query, params = prepare_query(
        """
        DELETE FROM tracing_projects
        WHERE id = $project_id
        """,
        project_id=project_id,
    )
    result = await conn.execute(query, *params)
    return result != "DELETE 0"
