"""Pytest configuration and fixtures for tests."""

import asyncio
import os
import subprocess
from collections.abc import AsyncGenerator

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.database import get_pool
from src.main import app

# Test database configuration
TEST_DB_NAME = "langsmith_test"
TEST_DB_USER = os.getenv("TEST_DB_USER", "postgres")
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "postgres")
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
TEST_DB_PORT = os.getenv("TEST_DB_PORT", "5432")

# Global connection pool
_pool = None


def pytest_configure(config):
    """Create test database and run migrations before any tests."""
    # Drop and create test database
    subprocess.run(
        [
            "psql",
            f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres",
            "-c",
            f"DROP DATABASE IF EXISTS {TEST_DB_NAME}",
        ],
        capture_output=True,
    )

    result = subprocess.run(
        [
            "psql",
            f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres",
            "-c",
            f"CREATE DATABASE {TEST_DB_NAME}",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test database: {result.stderr}")

    print(f"\n✓ Created test database: {TEST_DB_NAME}")

    # Run migrations
    test_db_url = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": test_db_url},
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to run migrations: {result.stderr}")

    print("✓ Ran database migrations")


def pytest_unconfigure(config):
    """Drop test database after all tests."""
    global _pool
    if _pool:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.run_until_complete(_pool.close())

    subprocess.run(
        [
            "psql",
            f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/postgres",
            "-c",
            f"DROP DATABASE IF EXISTS {TEST_DB_NAME}",
        ],
        capture_output=True,
    )
    print(f"\n✓ Dropped test database: {TEST_DB_NAME}")


async def get_test_pool():
    """Get or create the test database pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=TEST_DB_HOST,
            port=TEST_DB_PORT,
            user=TEST_DB_USER,
            password=TEST_DB_PASSWORD,
            database=TEST_DB_NAME,
            min_size=2,
            max_size=10,
        )
    return _pool


@pytest_asyncio.fixture
async def db_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection for a test with transaction rollback."""
    pool = await get_test_pool()
    async with pool.acquire() as conn:
        # Start a transaction
        async with conn.transaction():
            yield conn
            # Transaction is automatically rolled back


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""
    pool = await get_test_pool()

    # Override the database connection dependency
    app.dependency_overrides[get_pool] = lambda: pool

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_project(db_conn):
    """Create a sample project for testing."""
    row = await db_conn.fetchrow(
        """
        INSERT INTO tracing_projects (name)
        VALUES ($1)
        RETURNING id, name, created_at, modified_at
        """,
        "Test Project",
    )
    return dict(row)


@pytest_asyncio.fixture
async def sample_trace(db_conn, sample_project):
    """Create a sample trace for testing."""
    from datetime import datetime, timedelta

    import orjson

    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=1)

    row = await db_conn.fetchrow(
        """
        INSERT INTO traces (project_id, inputs, outputs, trace_metadata, start_time, end_time)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, project_id, inputs, outputs, trace_metadata, start_time, end_time
        """,
        sample_project["id"],
        orjson.dumps({"question": "What is 2+2?"}).decode(),
        orjson.dumps({"answer": "4"}).decode(),
        orjson.dumps({"model": "gpt-4"}).decode(),
        start_time,
        end_time,
    )
    result = dict(row)
    # Parse JSON fields
    for field in ["inputs", "outputs", "trace_metadata"]:
        if result[field] and isinstance(result[field], str):
            result[field] = orjson.loads(result[field])
    return result


@pytest_asyncio.fixture
async def sample_queue(db_conn):
    """Create a sample queue for testing."""
    row = await db_conn.fetchrow(
        """
        INSERT INTO queues (name)
        VALUES ($1)
        RETURNING id, name, created_at, modified_at
        """,
        "Test Queue",
    )
    return dict(row)


@pytest_asyncio.fixture
async def sample_rubric_item(db_conn, sample_queue):
    """Create a sample rubric item for testing."""
    row = await db_conn.fetchrow(
        """
        INSERT INTO queue_rubric_items (queue_id, feedback_key, description)
        VALUES ($1, $2, $3)
        RETURNING id, queue_id, feedback_key, description
        """,
        sample_queue["id"],
        "accuracy",
        "Is the answer accurate?",
    )
    return dict(row)


@pytest_asyncio.fixture
async def sample_queue_entry(db_conn, sample_queue, sample_trace):
    """Create a sample queue entry for testing."""
    row = await db_conn.fetchrow(
        """
        INSERT INTO queue_entries (queue_id, trace_id, status)
        VALUES ($1, $2, 'pending')
        RETURNING id, queue_id, trace_id, status, added_at
        """,
        sample_queue["id"],
        sample_trace["id"],
    )
    return dict(row)


@pytest_asyncio.fixture
async def sample_feedback(db_conn, sample_trace):
    """Create a sample feedback for testing."""
    row = await db_conn.fetchrow(
        """
        INSERT INTO feedback (trace_id, key, score, comment)
        VALUES ($1, $2, $3, $4)
        RETURNING id, trace_id, key, score, comment, created_at, modified_at
        """,
        sample_trace["id"],
        "accuracy",
        0.9,
        "Good answer",
    )
    return dict(row)
