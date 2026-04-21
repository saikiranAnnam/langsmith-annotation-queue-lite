"""Tests for rubrics endpoints."""

from httpx import AsyncClient


async def test_create_rubric_item(client: AsyncClient, sample_queue):
    """Test creating a rubric item."""
    response = await client.post(
        f"/queues/{sample_queue['id']}/rubric",
        json={"feedback_key": "helpfulness", "description": "Is the response helpful?"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["feedback_key"] == "helpfulness"
    assert data["description"] == "Is the response helpful?"
    assert data["queue_id"] == str(sample_queue["id"])
    assert "id" in data


async def test_create_rubric_item_queue_not_found(client: AsyncClient):
    """Test creating a rubric item for non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        f"/queues/{fake_id}/rubric", json={"feedback_key": "accuracy", "description": "Is it accurate?"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_create_rubric_item_duplicate_key(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test creating a rubric item with duplicate feedback_key."""
    response = await client.post(
        f"/queues/{sample_queue['id']}/rubric",
        json={"feedback_key": sample_rubric_item["feedback_key"], "description": "Another description"},
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_list_rubric_items(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test listing all rubric items for a queue."""
    response = await client.get(f"/queues/{sample_queue['id']}/rubric")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(r["id"] == str(sample_rubric_item["id"]) for r in data)


async def test_list_rubric_items_queue_not_found(client: AsyncClient):
    """Test listing rubric items for non-existent queue."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/queues/{fake_id}/rubric")

    assert response.status_code == 404
    assert response.json()["detail"] == "Queue not found"


async def test_list_rubric_items_empty(client: AsyncClient, sample_queue):
    """Test listing rubric items for queue with no items."""
    response = await client.get(f"/queues/{sample_queue['id']}/rubric")

    assert response.status_code == 200
    data = response.json()
    assert data == []


async def test_get_rubric_item(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test getting a specific rubric item."""
    response = await client.get(f"/queues/{sample_queue['id']}/rubric/{sample_rubric_item['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_rubric_item["id"])
    assert data["feedback_key"] == sample_rubric_item["feedback_key"]
    assert data["description"] == sample_rubric_item["description"]


async def test_get_rubric_item_not_found(client: AsyncClient, sample_queue):
    """Test getting a non-existent rubric item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/queues/{sample_queue['id']}/rubric/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Rubric item not found"


async def test_update_rubric_item(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test updating a rubric item."""
    response = await client.patch(
        f"/queues/{sample_queue['id']}/rubric/{sample_rubric_item['id']}",
        json={"description": "Updated description"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["id"] == str(sample_rubric_item["id"])
    assert data["feedback_key"] == sample_rubric_item["feedback_key"]


async def test_update_rubric_item_not_found(client: AsyncClient, sample_queue):
    """Test updating a non-existent rubric item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(
        f"/queues/{sample_queue['id']}/rubric/{fake_id}", json={"description": "New description"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Rubric item not found"


async def test_update_rubric_item_no_fields(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test updating a rubric item with no fields."""
    response = await client.patch(f"/queues/{sample_queue['id']}/rubric/{sample_rubric_item['id']}", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"


async def test_delete_rubric_item(client: AsyncClient, sample_queue, sample_rubric_item):
    """Test deleting a rubric item."""
    response = await client.delete(f"/queues/{sample_queue['id']}/rubric/{sample_rubric_item['id']}")

    assert response.status_code == 204

    # Verify rubric item is deleted
    response = await client.get(f"/queues/{sample_queue['id']}/rubric/{sample_rubric_item['id']}")
    assert response.status_code == 404


async def test_delete_rubric_item_not_found(client: AsyncClient, sample_queue):
    """Test deleting a non-existent rubric item."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/queues/{sample_queue['id']}/rubric/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Rubric item not found"
