"""Tests for queues endpoints."""

import asyncio
import os

import asyncpg
import orjson
from httpx import AsyncClient

_TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
_TEST_DB_PORT = int(os.getenv("TEST_DB_PORT", "5432"))
_TEST_DB_USER = os.getenv("TEST_DB_USER", "postgres")
_TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "postgres")
_TEST_DB_NAME = "langsmith_test"


async def test_create_queue(client: AsyncClient):
    """Test creating a new queue."""
    response = await client.post("/queues", json={"name": "My Test Queue"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Test Queue"
    assert "id" in data
    assert "created_at" in data
    assert "modified_at" in data
    assert data["pending_count"] == 0


async def test_list_queues(client: AsyncClient, sample_queue):
    """Test listing all queues."""
    response = await client.get("/queues")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(q["id"] == str(sample_queue["id"]) for q in data)
    # Check that pending_count is included
    for queue in data:
        assert "pending_count" in queue


async def test_get_queue(client: AsyncClient, sample_queue):
    """Test getting a specific queue."""
    response = await client.get(f"/queues/{sample_queue['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_queue["id"])
    assert data["name"] == sample_queue["name"]
    assert "pending_count" in data


async def test_get_queue_not_found(client: AsyncClient):
    """Test getting a non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/queues/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_update_queue(client: AsyncClient, sample_queue):
    """Test updating a queue."""
    response = await client.patch(f"/queues/{sample_queue['id']}", json={"name": "Updated Queue Name"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Queue Name"
    assert data["id"] == str(sample_queue["id"])


async def test_update_queue_not_found(client: AsyncClient):
    """Test updating a non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(f"/queues/{fake_id}", json={"name": "New Name"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_update_queue_no_fields(client: AsyncClient, sample_queue):
    """Test updating a queue with no fields."""
    response = await client.patch(f"/queues/{sample_queue['id']}", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


async def test_delete_queue(client: AsyncClient, sample_queue):
    """Test deleting a queue."""
    response = await client.delete(f"/queues/{sample_queue['id']}")

    assert response.status_code == 204

    # Verify queue is deleted
    response = await client.get(f"/queues/{sample_queue['id']}")
    assert response.status_code == 404


async def test_delete_queue_not_found(client: AsyncClient):
    """Test deleting a non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/queues/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_populate_queue(client: AsyncClient, sample_queue, sample_trace):
    """Test populating a queue with traces."""
    response = await client.post(
        f"/queues/{sample_queue['id']}/populate", json={"trace_ids": [str(sample_trace["id"])]}
    )

    assert response.status_code == 201
    data = response.json()
    assert "Added 1 entries to queue" in data["message"]

    # Verify queue now has pending entries
    response = await client.get(f"/queues/{sample_queue['id']}")
    data = response.json()
    assert data["pending_count"] == 1


async def test_populate_queue_multiple_traces(client: AsyncClient, sample_queue, sample_trace, db_conn, sample_project):
    """Test populating a queue with multiple traces."""
    from datetime import datetime

    import orjson

    # Create another trace
    row = await db_conn.fetchrow(
        """
        INSERT INTO traces (project_id, inputs, outputs, start_time)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        sample_project["id"],
        orjson.dumps({"question": "test2"}).decode(),
        orjson.dumps({"answer": "test2"}).decode(),
        datetime.now(),
    )
    trace2_id = row["id"]

    response = await client.post(
        f"/queues/{sample_queue['id']}/populate", json={"trace_ids": [str(sample_trace["id"]), str(trace2_id)]}
    )

    assert response.status_code == 201
    data = response.json()
    assert "Added 2 entries to queue" in data["message"]


async def test_populate_queue_not_found(client: AsyncClient, sample_trace):
    """Test populating a non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{fake_id}/populate", json={"trace_ids": [str(sample_trace["id"])]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_populate_queue_trace_not_found(client: AsyncClient, sample_queue):
    """Test populating a queue with non-existent traces."""
    fake_trace_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{sample_queue['id']}/populate", json={"trace_ids": [fake_trace_id]})

    assert response.status_code == 404
    assert "Traces not found" in response.json()["detail"]


async def test_get_next_entry(client: AsyncClient, sample_queue_entry):
    """Test getting the next entry from a queue."""
    """in_progress status is set when the entry is reserved."""
    response = await client.get(f"/queues/{sample_queue_entry['queue_id']}/entries/next")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_queue_entry["id"])
    assert data["status"] == "in_progress"
    assert "trace" in data
    assert data["trace"]["id"] == str(sample_queue_entry["trace_id"])


async def test_get_next_entry_empty_queue(client: AsyncClient, sample_queue):
    """Test getting next entry from an empty queue."""
    """No pending entries in queue is returned when the queue is empty."""
    response = await client.get(f"/queues/{sample_queue['id']}/entries/next")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue is empty"


async def test_get_next_entry_queue_not_found(client: AsyncClient):
    """Test getting next entry from non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/queues/{fake_id}/entries/next")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_get_next_entry_sets_in_progress(client: AsyncClient, sample_queue_entry):
    """Test getting next entry sets the entry to reserved and mark it in_progress status."""
    response = await client.get(f"/queues/{sample_queue_entry['queue_id']}/entries/next")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_queue_entry["id"])
    assert data["status"] == "in_progress"
    assert data["reserved_at"] is not None
    assert data["reserved_by"] is not None


async def test_get_next_entry_fifo_order(client: AsyncClient, sample_queue, db_conn, sample_project):
    """Test that entries are returned in FIFO order."""
    from datetime import datetime, timedelta

    import orjson

    # Create two traces
    trace1 = await db_conn.fetchrow(
        """
        INSERT INTO traces (project_id, inputs, outputs, start_time)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        sample_project["id"],
        orjson.dumps({"question": "first"}).decode(),
        orjson.dumps({"answer": "first"}).decode(),
        datetime.now(),
    )

    trace2 = await db_conn.fetchrow(
        """
        INSERT INTO traces (project_id, inputs, outputs, start_time)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        sample_project["id"],
        orjson.dumps({"question": "second"}).decode(),
        orjson.dumps({"answer": "second"}).decode(),
        datetime.now(),
    )

    # Add to queue with specific order
    entry1 = await db_conn.fetchrow(
        """
        INSERT INTO queue_entries (queue_id, trace_id, status, added_at)
        VALUES ($1, $2, 'pending', $3)
        RETURNING id
        """,
        sample_queue["id"],
        trace1["id"],
        datetime.now(),
    )

    await db_conn.fetchrow(
        """
        INSERT INTO queue_entries (queue_id, trace_id, status, added_at)
        VALUES ($1, $2, 'pending', $3)
        RETURNING id
        """,
        sample_queue["id"],
        trace2["id"],
        datetime.now() + timedelta(seconds=1),
    )

    # First call should return first entry
    response = await client.get(f"/queues/{sample_queue['id']}/entries/next")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(entry1["id"])


async def test_complete_entry(client: AsyncClient, sample_queue, sample_queue_entry):
    """Test completing a queue entry."""
    response = await client.post(f"/queues/{sample_queue['id']}/entries/{sample_queue_entry['id']}/complete")

    assert response.status_code == 200
    data = response.json()
    assert "completed" in data["message"]

    # Verify no pending entries remain (completed entry is not re-served)
    response = await client.get(f"/queues/{sample_queue['id']}/entries/next")
    assert response.status_code == 404


async def test_complete_entry_not_found(client: AsyncClient, sample_queue):
    """Test completing a non-existent entry."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{sample_queue['id']}/entries/{fake_id}/complete")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue entry not found"


async def test_complete_entry_queue_not_found(client: AsyncClient, sample_queue_entry):
    """Test completing an entry with non-existent queue."""
    fake_queue_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{fake_queue_id}/entries/{sample_queue_entry['id']}/complete")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_requeue_entry(client: AsyncClient, sample_queue, sample_queue_entry):
    """Test requeuing an entry."""
    # Requeue the entry
    response = await client.post(f"/queues/{sample_queue['id']}/entries/{sample_queue_entry['id']}/requeue")

    assert response.status_code == 200
    data = response.json()
    assert "requeued" in data["message"]

    # Verify entry is pending again
    response = await client.get(f"/queues/{sample_queue['id']}")
    data = response.json()
    assert data["pending_count"] == 1


async def test_requeue_entry_not_found(client: AsyncClient, sample_queue):
    """Test requeuing a non-existent entry."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{sample_queue['id']}/entries/{fake_id}/requeue")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue entry not found"


async def test_requeue_entry_queue_not_found(client: AsyncClient, sample_queue_entry):
    """Test requeuing an entry with non-existent queue."""
    fake_queue_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(f"/queues/{fake_queue_id}/entries/{sample_queue_entry['id']}/requeue")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_get_next_entry_excludes_in_progress(client: AsyncClient, sample_queue, sample_queue_entry):
    """An in_progress entry is not returned to a different reviewer as the next entry."""
    # Reserve the only entry as reviewer-A
    response = await client.get(
        f"/queues/{sample_queue['id']}/entries/next?reviewer_id=reviewer-a"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    # A different reviewer should see an empty queue — the in_progress entry must be excluded
    response = await client.get(
        f"/queues/{sample_queue['id']}/entries/next?reviewer_id=reviewer-b"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Queue is empty"


async def test_get_next_entry_idempotent_for_same_reviewer(client: AsyncClient, sample_queue, sample_queue_entry):
    """Calling get_next_entry twice with the same reviewer_id returns the same entry both times."""
    first = await client.get(
        f"/queues/{sample_queue['id']}/entries/next?reviewer_id=reviewer-a"
    )
    assert first.status_code == 200
    first_entry_id = first.json()["id"]

    # Second call — same reviewer, same queue
    second = await client.get(
        f"/queues/{sample_queue['id']}/entries/next?reviewer_id=reviewer-a"
    )
    assert second.status_code == 200
    assert second.json()["id"] == first_entry_id


async def test_concurrent_reservation_no_duplicate():
    """Two reviewers calling get_next_entry simultaneously each get a different entry.

    This test bypasses the transaction-rollback fixture because FOR UPDATE SKIP LOCKED
    only prevents duplicate reservations across separate connections — it can't be
    demonstrated within a single connection's transaction. The test creates its own
    pool, commits real rows, runs concurrent reservations, and cleans up afterwards.
    """
    from datetime import datetime

    from src.services.queues import get_next_entry

    pool = await asyncpg.create_pool(
        host=_TEST_DB_HOST,
        port=_TEST_DB_PORT,
        user=_TEST_DB_USER,
        password=_TEST_DB_PASSWORD,
        database=_TEST_DB_NAME,
        min_size=2,
        max_size=5,
    )

    project_id = None
    queue_id = None
    try:
        async with pool.acquire() as conn:
            proj = await conn.fetchrow(
                "INSERT INTO tracing_projects (name) VALUES ($1) RETURNING id",
                "concurrent-reservation-test",
            )
            project_id = proj["id"]

            t1 = await conn.fetchrow(
                "INSERT INTO traces (project_id, inputs, outputs, start_time) VALUES ($1, $2, $3, $4) RETURNING id",
                project_id,
                orjson.dumps({"q": "first"}).decode(),
                orjson.dumps({"a": "first"}).decode(),
                datetime.now(),
            )
            t2 = await conn.fetchrow(
                "INSERT INTO traces (project_id, inputs, outputs, start_time) VALUES ($1, $2, $3, $4) RETURNING id",
                project_id,
                orjson.dumps({"q": "second"}).decode(),
                orjson.dumps({"a": "second"}).decode(),
                datetime.now(),
            )

            q = await conn.fetchrow(
                "INSERT INTO queues (name) VALUES ($1) RETURNING id",
                "concurrent-reservation-test-queue",
            )
            queue_id = q["id"]

            await conn.executemany(
                "INSERT INTO queue_entries (queue_id, trace_id, status) VALUES ($1, $2, 'pending')",
                [(queue_id, t1["id"]), (queue_id, t2["id"])],
            )

        async def reserve(reviewer_id: str):
            async with pool.acquire() as conn:
                return await get_next_entry(conn, queue_id, reviewer_id)

        entry_a, entry_b = await asyncio.gather(
            reserve("reviewer-a"),
            reserve("reviewer-b"),
        )

        # Both reviewers got an entry and each got a different one.
        assert entry_a is not None and entry_a is not False
        assert entry_b is not None and entry_b is not False
        assert entry_a["id"] != entry_b["id"], "FOR UPDATE SKIP LOCKED must give each reviewer a distinct entry"
        assert entry_a["status"] == "in_progress"
        assert entry_b["status"] == "in_progress"

    finally:
        async with pool.acquire() as conn:
            if queue_id:
                await conn.execute("DELETE FROM queues WHERE id = $1", queue_id)
            if project_id:
                # Cascades to traces → queue_entries
                await conn.execute("DELETE FROM tracing_projects WHERE id = $1", project_id)
        await pool.close()
