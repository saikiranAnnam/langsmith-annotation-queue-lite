"""Tests for traces endpoints."""

from datetime import datetime, timedelta

from httpx import AsyncClient


async def test_create_trace(client: AsyncClient, sample_project):
    """Test creating a new trace."""
    start_time = datetime.now().isoformat()
    end_time = (datetime.now() + timedelta(seconds=2)).isoformat()

    response = await client.post(
        "/traces",
        json={
            "project_id": str(sample_project["id"]),
            "inputs": {"question": "What is the capital of France?"},
            "outputs": {"answer": "Paris"},
            "trace_metadata": {"model": "gpt-4", "tokens": 25},
            "start_time": start_time,
            "end_time": end_time,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(sample_project["id"])
    assert data["inputs"]["question"] == "What is the capital of France?"
    assert data["outputs"]["answer"] == "Paris"
    assert data["trace_metadata"]["model"] == "gpt-4"
    assert "id" in data


async def test_create_trace_project_not_found(client: AsyncClient):
    """Test creating a trace with non-existent project."""
    fake_project_id = "00000000-0000-0000-0000-000000000000"
    start_time = datetime.now().isoformat()

    response = await client.post(
        "/traces",
        json={
            "project_id": fake_project_id,
            "inputs": {"question": "Test"},
            "outputs": {"answer": "Test"},
            "start_time": start_time,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


async def test_create_trace_minimal(client: AsyncClient, sample_project):
    """Test creating a trace with minimal fields."""
    start_time = datetime.now().isoformat()

    response = await client.post(
        "/traces",
        json={
            "project_id": str(sample_project["id"]),
            "start_time": start_time,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["project_id"] == str(sample_project["id"])
    assert data["inputs"] is None
    assert data["outputs"] is None
    assert data["trace_metadata"] is None
    assert data["end_time"] is None


async def test_get_trace(client: AsyncClient, sample_trace):
    """Test getting a specific trace."""
    response = await client.get(f"/traces/{sample_trace['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_trace["id"])
    assert data["project_id"] == str(sample_trace["project_id"])


async def test_get_trace_not_found(client: AsyncClient):
    """Test getting a non-existent trace."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/traces/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trace not found"


async def test_query_traces_by_project(client: AsyncClient, sample_project, sample_trace):
    """Test querying traces by project_id."""
    response = await client.post("/traces/query", json={"project_id": str(sample_project["id"])})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(t["id"] == str(sample_trace["id"]) for t in data)


async def test_query_traces_by_trace_ids(client: AsyncClient, sample_trace):
    """Test querying traces by trace_ids."""
    response = await client.post("/traces/query", json={"trace_ids": [str(sample_trace["id"])]})

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == str(sample_trace["id"])


async def test_query_traces_by_session_id(client: AsyncClient, db_conn, sample_project):
    """Test querying traces by session_id in metadata."""
    from datetime import datetime

    import orjson

    # Create trace with session_id in metadata
    session_id = "test-session-123"
    row = await db_conn.fetchrow(
        """
        INSERT INTO traces (project_id, inputs, outputs, trace_metadata, start_time)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        sample_project["id"],
        orjson.dumps({"question": "test"}).decode(),
        orjson.dumps({"answer": "test"}).decode(),
        orjson.dumps({"session_id": session_id}).decode(),
        datetime.now(),
    )
    trace_id = row["id"]

    response = await client.post("/traces/query", json={"session_id": session_id})

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(t["id"] == str(trace_id) for t in data)


async def test_query_traces_empty_result(client: AsyncClient):
    """Test querying traces with no matches."""
    fake_project_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post("/traces/query", json={"project_id": fake_project_id})

    assert response.status_code == 200
    data = response.json()
    assert data == []


async def test_query_traces_no_filters(client: AsyncClient):
    """Test querying traces without any filters returns empty."""
    response = await client.post("/traces/query", json={})

    assert response.status_code == 200
    data = response.json()
    assert data == []
