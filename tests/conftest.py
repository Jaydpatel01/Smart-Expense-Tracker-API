"""pytest configuration and fixtures for API testing."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


@pytest_asyncio.fixture
async def async_client():
    """Fixture providing an async HTTP client for API testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
