"""Tests for projects endpoints."""

from httpx import AsyncClient


async def test_create_project(client: AsyncClient):
    """Test creating a new project."""
    response = await client.post("/projects", json={"name": "My Project"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Project"
    assert "id" in data
    assert "created_at" in data
    assert "modified_at" in data


async def test_list_projects(client: AsyncClient, sample_project):
    """Test listing all projects."""
    response = await client.get("/projects")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == str(sample_project["id"]) for p in data)


async def test_get_project(client: AsyncClient, sample_project):
    """Test getting a specific project."""
    response = await client.get(f"/projects/{sample_project['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_project["id"])
    assert data["name"] == sample_project["name"]


async def test_get_project_not_found(client: AsyncClient):
    """Test getting a non-existent project."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/projects/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


async def test_delete_project(client: AsyncClient, sample_project):
    """Test deleting a project."""
    response = await client.delete(f"/projects/{sample_project['id']}")

    assert response.status_code == 204

    # Verify project is deleted
    response = await client.get(f"/projects/{sample_project['id']}")
    assert response.status_code == 404


async def test_delete_project_not_found(client: AsyncClient):
    """Test deleting a non-existent project."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/projects/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


async def test_delete_project_cascades_to_traces(client: AsyncClient, sample_project, sample_trace):
    """Test that deleting a project cascades to traces."""
    # Verify trace exists
    response = await client.get(f"/traces/{sample_trace['id']}")
    assert response.status_code == 200

    # Delete project
    response = await client.delete(f"/projects/{sample_project['id']}")
    assert response.status_code == 204

    # Verify trace is also deleted
    response = await client.get(f"/traces/{sample_trace['id']}")
    assert response.status_code == 404
