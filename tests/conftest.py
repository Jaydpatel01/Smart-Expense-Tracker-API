"""pytest configuration and fixtures for API testing."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from main import app
import storage as storage_module


@pytest_asyncio.fixture
async def async_client():
    """Async HTTPX client fixture used by existing async integration tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Synchronous TestClient fixture with isolated per-test storage.

    Sets EXPENSE_DATA_PATH to a unique temp file and patches the storage singleton
    so that every test starts with a completely empty data file.
    Tears down the temp file after each test automatically via tmp_path.
    """
    temp_file = tmp_path / "test_expenses.json"
    monkeypatch.setenv("EXPENSE_DATA_PATH", str(temp_file))

    # Re-point the module-level singleton so services.py always reads/writes the temp file
    storage_module.storage.file_path = temp_file

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
