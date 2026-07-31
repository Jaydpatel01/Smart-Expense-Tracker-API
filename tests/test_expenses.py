"""Integration and unit tests for expense endpoints."""

from datetime import date
import pytest
from storage import ExpenseStorage


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path, monkeypatch):
    """Automatically isolate storage for all endpoint integration tests."""
    test_file = tmp_path / "test_api_expenses.json"
    monkeypatch.setenv("EXPENSE_DATA_PATH", str(test_file))
    # Reset storage singleton to point to temporary test file
    from storage import storage
    storage.file_path = test_file


@pytest.mark.anyio
async def test_health_check(async_client):
    """Test root health check endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.anyio
async def test_create_expense_success(async_client):
    """Test POST /expenses endpoint creates a valid expense."""
    payload = {
        "title": "  Supermarket Groceries  ",
        "amount": 75.50,
        "category": "food",
        "date": date.today().isoformat(),
    }
    response = await async_client.post("/expenses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Supermarket Groceries"
    assert data["amount"] == 75.50
    assert data["category"] == "food"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_expense_validation_errors(async_client):
    """Test POST /expenses validation errors for invalid input payloads."""
    # Negative amount
    res1 = await async_client.post(
        "/expenses",
        json={
            "title": "Invalid Amount",
            "amount": -10.0,
            "category": "food",
            "date": date.today().isoformat(),
        },
    )
    assert res1.status_code == 422

    # Empty title
    res2 = await async_client.post(
        "/expenses",
        json={
            "title": "   ",
            "amount": 10.0,
            "category": "food",
            "date": date.today().isoformat(),
        },
    )
    assert res2.status_code == 422

    # Invalid category
    res3 = await async_client.post(
        "/expenses",
        json={
            "title": "Flight Ticket",
            "amount": 200.0,
            "category": "travel",
            "date": date.today().isoformat(),
        },
    )
    assert res3.status_code == 422


@pytest.mark.anyio
async def test_get_expenses_and_filtering(async_client):
    """Test GET /expenses with and without category filter."""
    today = date.today().isoformat()
    await async_client.post(
        "/expenses",
        json={"title": "Coffee", "amount": 4.50, "category": "food", "date": today},
    )
    await async_client.post(
        "/expenses",
        json={"title": "Bus", "amount": 2.50, "category": "transport", "date": today},
    )

    # Get all expenses
    res_all = await async_client.get("/expenses")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # Filter by category
    res_food = await async_client.get("/expenses?category=food")
    assert res_food.status_code == 200
    assert len(res_food.json()) == 1
    assert res_food.json()[0]["title"] == "Coffee"

    # Filter by invalid category
    res_invalid = await async_client.get("/expenses?category=invalid_cat")
    assert res_invalid.status_code == 400
    assert "Invalid category" in res_invalid.json()["detail"]


@pytest.mark.anyio
async def test_get_totals(async_client):
    """Test GET /expenses/totals endpoint."""
    today = date.today().isoformat()
    await async_client.post(
        "/expenses",
        json={"title": "Lunch", "amount": 20.00, "category": "food", "date": today},
    )
    await async_client.post(
        "/expenses",
        json={"title": "Train", "amount": 10.00, "category": "transport", "date": today},
    )

    # Overall totals
    res_total = await async_client.get("/expenses/totals")
    assert res_total.status_code == 200
    data = res_total.json()
    assert data["total"] == 30.00
    assert data["by_category"]["food"] == 20.00
    assert data["by_category"]["transport"] == 10.00

    # Filtered total
    res_food_total = await async_client.get("/expenses/totals?category=food")
    assert res_food_total.status_code == 200
    assert res_food_total.json()["total"] == 20.00

    # Invalid category
    res_invalid = await async_client.get("/expenses/totals?category=unknown")
    assert res_invalid.status_code == 400


@pytest.mark.anyio
async def test_delete_expense(async_client):
    """Test DELETE /expenses/{expense_id} endpoint."""
    today = date.today().isoformat()
    created_res = await async_client.post(
        "/expenses",
        json={"title": "Movie", "amount": 15.00, "category": "entertainment", "date": today},
    )
    expense_id = created_res.json()["id"]

    # Delete existing expense
    delete_res = await async_client.delete(f"/expenses/{expense_id}")
    assert delete_res.status_code == 204

    # Verify expense is deleted
    get_res = await async_client.get("/expenses")
    assert len(get_res.json()) == 0

    # Delete non-existent expense
    missing_res = await async_client.delete("/expenses/non-existent-uuid")
    assert missing_res.status_code == 404
    assert missing_res.json()["detail"] == "Expense not found"
