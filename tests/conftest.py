"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for async endpoints."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
