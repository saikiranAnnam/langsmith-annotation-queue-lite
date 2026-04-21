"""Tests for queues endpoints."""

from httpx import AsyncClient


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
    response = await client.get(f"/queues/{sample_queue_entry['queue_id']}/entries/next")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_queue_entry["id"])
    assert data["status"] == "pending"
    assert "trace" in data
    assert data["trace"]["id"] == str(sample_queue_entry["trace_id"])


async def test_get_next_entry_empty_queue(client: AsyncClient, sample_queue):
    """Test getting next entry from an empty queue."""
    response = await client.get(f"/queues/{sample_queue['id']}/entries/next")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue is empty"


async def test_get_next_entry_queue_not_found(client: AsyncClient):
    """Test getting next entry from non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/queues/{fake_id}/entries/next")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


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
    assert "completed and removed" in data["message"]

    # Verify entry is deleted
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
