"""Tests for MCP routes."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


def test_health_endpoint(client: TestClient):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_tools(client: TestClient):
    """Test GET /mcp/tools endpoint."""
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)
    
    # Check for expected tools
    tool_names = [tool["name"] for tool in data["tools"]]
    assert "web_search" in tool_names
    assert "fetch_page" in tool_names


def test_web_search_missing_query(client: TestClient):
    """Test web_search with missing required query parameter."""
    response = client.post("/mcp/tools/web_search", json={})
    assert response.status_code == 422


def test_web_search_invalid_num_results(client: TestClient):
    """Test web_search with invalid num_results (out of range)."""
    response = client.post(
        "/mcp/tools/web_search",
        json={"query": "test", "num_results": 100}
    )
    assert response.status_code == 422


def test_fetch_page_missing_url(client: TestClient):
    """Test fetch_page with missing required url parameter."""
    response = client.post("/mcp/tools/fetch_page", json={})
    assert response.status_code == 422


def test_web_search_valid_request(client: TestClient):
    """Test web_search with valid request."""
    response = client.post(
        "/mcp/tools/web_search",
        json={
            "query": "python programming",
            "num_results": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)
