"""Tests for feedback endpoints."""

from httpx import AsyncClient


async def test_create_feedback_batch(client: AsyncClient, sample_trace):
    """Test creating multiple feedback items at once."""
    response = await client.post(
        "/feedback/batch",
        json=[
            {
                "trace_id": str(sample_trace["id"]),
                "key": "accuracy",
                "score": 0.9,
                "comment": "Very accurate",
            },
            {
                "trace_id": str(sample_trace["id"]),
                "key": "helpfulness",
                "score": 0.8,
                "comment": "Quite helpful",
            },
        ],
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["key"] == "accuracy"
    assert data[0]["score"] == 0.9
    assert data[1]["key"] == "helpfulness"
    assert data[1]["score"] == 0.8


async def test_create_feedback_batch_empty(client: AsyncClient):
    """Test creating an empty feedback batch."""
    response = await client.post("/feedback/batch", json=[])

    assert response.status_code == 400
    assert response.json()["detail"] == "Feedback batch cannot be empty"


async def test_create_feedback_batch_trace_not_found(client: AsyncClient):
    """Test creating feedback for non-existent trace."""
    fake_trace_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/feedback/batch",
        json=[
            {
                "trace_id": fake_trace_id,
                "key": "accuracy",
                "score": 0.9,
            }
        ],
    )

    assert response.status_code == 404
    assert "Traces not found" in response.json()["detail"]


async def test_create_feedback_batch_minimal(client: AsyncClient, sample_trace):
    """Test creating feedback with minimal fields."""
    response = await client.post(
        "/feedback/batch",
        json=[
            {
                "trace_id": str(sample_trace["id"]),
                "key": "test_key",
            }
        ],
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["key"] == "test_key"
    assert data[0]["score"] is None
    assert data[0]["comment"] is None


async def test_get_feedback(client: AsyncClient, sample_feedback):
    """Test getting a specific feedback item."""
    response = await client.get(f"/feedback/{sample_feedback['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_feedback["id"])
    assert data["trace_id"] == str(sample_feedback["trace_id"])
    assert data["key"] == sample_feedback["key"]
    assert data["score"] == sample_feedback["score"]


async def test_get_feedback_not_found(client: AsyncClient):
    """Test getting a non-existent feedback item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/feedback/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Feedback not found"


async def test_update_feedback_score(client: AsyncClient, sample_feedback):
    """Test updating feedback score."""
    response = await client.patch(f"/feedback/{sample_feedback['id']}", json={"score": 0.95})

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0.95
    assert data["id"] == str(sample_feedback["id"])


async def test_update_feedback_comment(client: AsyncClient, sample_feedback):
    """Test updating feedback comment."""
    response = await client.patch(f"/feedback/{sample_feedback['id']}", json={"comment": "Updated comment"})

    assert response.status_code == 200
    data = response.json()
    assert data["comment"] == "Updated comment"
    assert data["id"] == str(sample_feedback["id"])


async def test_update_feedback_multiple_fields(client: AsyncClient, sample_feedback):
    """Test updating multiple feedback fields at once."""
    response = await client.patch(
        f"/feedback/{sample_feedback['id']}",
        json={"score": 0.75, "comment": "Updated both"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0.75
    assert data["comment"] == "Updated both"


async def test_update_feedback_not_found(client: AsyncClient):
    """Test updating a non-existent feedback item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(f"/feedback/{fake_id}", json={"score": 0.5})

    assert response.status_code == 404
    assert response.json()["detail"] == "Feedback not found"


async def test_update_feedback_no_fields(client: AsyncClient, sample_feedback):
    """Test updating feedback with no fields."""
    response = await client.patch(f"/feedback/{sample_feedback['id']}", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


async def test_delete_feedback(client: AsyncClient, sample_feedback):
    """Test deleting a feedback item."""
    response = await client.delete(f"/feedback/{sample_feedback['id']}")

    assert response.status_code == 204

    # Verify feedback is deleted
    response = await client.get(f"/feedback/{sample_feedback['id']}")
    assert response.status_code == 404


async def test_delete_feedback_not_found(client: AsyncClient):
    """Test deleting a non-existent feedback item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/feedback/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Feedback not found"


async def test_feedback_cascade_delete_with_trace(client: AsyncClient, sample_trace, sample_feedback, db_conn):
    """Test that feedback is deleted when trace is deleted."""
    # Verify feedback exists
    response = await client.get(f"/feedback/{sample_feedback['id']}")
    assert response.status_code == 200

    # Delete the trace
    await db_conn.execute("DELETE FROM traces WHERE id = $1", sample_trace["id"])

    # Verify feedback is also deleted
    response = await client.get(f"/feedback/{sample_feedback['id']}")
    assert response.status_code == 404
