"""Tests for MCP routes."""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from app.routes import mcp


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


def test_mcp_initialize_jsonrpc(client: TestClient):
    """POST /mcp should support JSON-RPC initialize."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert data["result"]["capabilities"] == {"tools": {}}


def test_mcp_tools_list_jsonrpc(client: TestClient):
    """POST /mcp tools/list should return tool definitions."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": "abc",
            "method": "tools/list",
            "params": {},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "abc"
    assert "tools" in data["result"]
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "web_search" in tool_names
    assert "fetch_page" in tool_names


def test_mcp_tools_call_jsonrpc(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """POST /mcp tools/call should execute tool and return MCP content."""

    async def fake_execute_tool(tool_name: str, tool_input: dict):
        if tool_name == "web_search":
            return {"results": [{"title": "A", "url": "https://example.com", "snippet": "S"}]}
        return {"title": "T", "content": "C", "url": "https://example.com"}

    monkeypatch.setattr(mcp, "_execute_tool", fake_execute_tool)

    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {"query": "python", "num_results": 1},
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert data["result"]["isError"] is False
    assert data["result"]["content"][0]["type"] == "text"


def test_mcp_tools_call_web_search_with_mocked_service(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    """POST /mcp tools/call should pass through to search service with mocked dependency."""

    async def fake_search(query: str, num_results: int = 5):
        return [
            {
                "title": "Mock title",
                "url": "https://example.com/mock",
                "snippet": f"query={query}, n={num_results}",
            }
        ]

    monkeypatch.setattr(mcp.search_service, "search", fake_search)

    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {"query": "mcp", "num_results": 2},
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 3
    payload = json.loads(data["result"]["content"][0]["text"])
    assert payload["results"][0]["url"] == "https://example.com/mock"
    assert payload["results"][0]["snippet"] == "query=mcp, n=2"


def test_mcp_method_not_found(client: TestClient):
    """POST /mcp should return JSON-RPC error for unknown method."""
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 77,
            "method": "unknown/method",
            "params": {},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 77
    assert data["error"]["code"] == -32601


def test_sse_generator_first_event_is_endpoint():
    """SSE generator should emit legacy endpoint event first for fallback clients."""

    async def _first_event() -> str:
        gen = mcp.sse_generator()
        first = await anext(gen)
        await gen.aclose()
        return first

    first_chunk = asyncio.run(_first_event())
    assert "event: endpoint" in first_chunk
    assert "data: /mcp" in first_chunk
