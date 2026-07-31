"""Integration and unit tests for expense endpoints and functionality."""

import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test root health check endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
