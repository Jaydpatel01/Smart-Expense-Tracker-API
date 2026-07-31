"""Comprehensive integration tests for the Smart Expense Tracker API expense endpoints."""

from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
FUTURE_DATE = (date.today() + timedelta(days=1)).isoformat()


def _expense_payload(
    title: str = "Groceries",
    amount: float = 50.00,
    category: str = "food",
    expense_date: str = TODAY,
) -> dict:
    """Build a minimal valid expense payload with sensible defaults."""
    return {"title": title, "amount": amount, "category": category, "date": expense_date}


def _post_expense(client, **kwargs) -> dict:
    """Post a single expense and assert 201; return the response JSON."""
    res = client.post("/expenses", json=_expense_payload(**kwargs))
    assert res.status_code == 201, res.text
    return res.json()


# ===========================================================================
# HAPPY PATH TESTS
# ===========================================================================


class TestCreateExpense:
    """POST /expenses — happy path."""

    def test_create_expense_returns_201_with_all_fields(self, client):
        """Creating a valid expense returns 201 and a response with all expected fields."""
        payload = _expense_payload(
            title="  Supermarket  ",
            amount=99.99,
            category="food",
            expense_date=TODAY,
        )
        res = client.post("/expenses", json=payload)

        assert res.status_code == 201
        data = res.json()

        # Core fields
        assert data["title"] == "Supermarket"  # whitespace stripped
        assert data["amount"] == 99.99
        assert data["category"] == "food"
        assert data["date"] == TODAY

        # Auto-generated fields
        assert "id" in data
        assert len(data["id"]) == 36  # UUID v4
        assert "created_at" in data


class TestGetExpenses:
    """GET /expenses — happy path."""

    def test_get_expenses_returns_empty_list_when_no_data(self, client):
        """GET /expenses returns an empty list when no expenses have been added."""
        res = client.get("/expenses")

        assert res.status_code == 200
        assert res.json() == []

    def test_get_expenses_returns_all_after_adding_several(self, client):
        """GET /expenses returns all added expenses."""
        _post_expense(client, title="Coffee", category="food", amount=4.50)
        _post_expense(client, title="Bus", category="transport", amount=2.50)
        _post_expense(client, title="Rent", category="housing", amount=1200.00)

        res = client.get("/expenses")

        assert res.status_code == 200
        titles = {e["title"] for e in res.json()}
        assert titles == {"Coffee", "Bus", "Rent"}

    def test_get_expenses_sorted_by_date_descending(self, client):
        """GET /expenses returns expenses ordered by date descending."""
        _post_expense(client, title="Old Expense", expense_date=YESTERDAY)
        _post_expense(client, title="New Expense", expense_date=TODAY)

        res = client.get("/expenses")
        dates = [e["date"] for e in res.json()]

        assert dates == sorted(dates, reverse=True)

    def test_get_expenses_filter_by_category_returns_only_matching(self, client):
        """GET /expenses?category=food returns only expenses in the food category."""
        _post_expense(client, title="Pizza", category="food")
        _post_expense(client, title="Taxi", category="transport")
        _post_expense(client, title="Salad", category="food")

        res = client.get("/expenses", params={"category": "food"})

        assert res.status_code == 200
        results = res.json()
        assert len(results) == 2
        assert all(e["category"] == "food" for e in results)
        titles = {e["title"] for e in results}
        assert titles == {"Pizza", "Salad"}


class TestGetTotals:
    """GET /expenses/totals — happy path."""

    def test_totals_returns_correct_overall_total(self, client):
        """GET /expenses/totals sums all expenses correctly."""
        _post_expense(client, title="Lunch", amount=20.00, category="food")
        _post_expense(client, title="Train", amount=10.50, category="transport")
        _post_expense(client, title="Gym", amount=45.00, category="health")

        expected_total = round(20.00 + 10.50 + 45.00, 2)

        res = client.get("/expenses/totals")

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == expected_total

    def test_totals_returns_correct_by_category_breakdown(self, client):
        """GET /expenses/totals by_category contains correct per-category sums."""
        _post_expense(client, title="Coffee", amount=4.00, category="food")
        _post_expense(client, title="Dinner", amount=36.00, category="food")
        _post_expense(client, title="Metro", amount=2.50, category="transport")

        res = client.get("/expenses/totals")

        assert res.status_code == 200
        by_cat = res.json()["by_category"]
        assert by_cat["food"] == round(4.00 + 36.00, 2)
        assert by_cat["transport"] == 2.50

    def test_totals_filtered_by_category_returns_only_that_category(self, client):
        """GET /expenses/totals?category=food returns total for food only."""
        food_amount_1 = 25.00
        food_amount_2 = 15.00
        _post_expense(client, title="Breakfast", amount=food_amount_1, category="food")
        _post_expense(client, title="Snacks", amount=food_amount_2, category="food")
        _post_expense(client, title="Bus", amount=5.00, category="transport")

        expected_food_total = round(food_amount_1 + food_amount_2, 2)

        res = client.get("/expenses/totals", params={"category": "food"})

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == expected_food_total
        assert list(data["by_category"].keys()) == ["food"]
        assert data["by_category"]["food"] == expected_food_total


class TestDeleteExpense:
    """DELETE /expenses/{id} — happy path."""

    def test_delete_existing_expense_returns_204_and_removes_it(self, client):
        """DELETE /expenses/{id} returns 204 and expense no longer appears in GET."""
        created = _post_expense(client, title="Movie Ticket", category="entertainment")
        expense_id = created["id"]

        del_res = client.delete(f"/expenses/{expense_id}")
        assert del_res.status_code == 204

        # Verify it's gone
        get_res = client.get("/expenses")
        ids = [e["id"] for e in get_res.json()]
        assert expense_id not in ids


# ===========================================================================
# VALIDATION / EDGE CASE TESTS
# ===========================================================================


class TestCreateExpenseValidation:
    """POST /expenses — validation failures."""

    def test_amount_zero_returns_422(self, client):
        """POST with amount = 0 must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(amount=0))
        assert res.status_code == 422

    def test_amount_negative_returns_422(self, client):
        """POST with amount = -5 must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(amount=-5))
        assert res.status_code == 422

    def test_empty_title_returns_422(self, client):
        """POST with empty string title must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(title=""))
        assert res.status_code == 422

    def test_whitespace_only_title_returns_422(self, client):
        """POST with whitespace-only title must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(title="     "))
        assert res.status_code == 422

    def test_invalid_category_returns_422(self, client):
        """POST with a category not in the allowed list must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(category="travel"))
        assert res.status_code == 422

    def test_future_date_returns_422(self, client):
        """POST with a future date must be rejected with 422."""
        res = client.post("/expenses", json=_expense_payload(expense_date=FUTURE_DATE))
        assert res.status_code == 422

    def test_invalid_date_format_returns_422(self, client):
        """POST with date in DD-MM-YYYY format (not ISO 8601) must be rejected with 422."""
        invalid_date = "25-12-2024"
        res = client.post("/expenses", json=_expense_payload(expense_date=invalid_date))
        assert res.status_code == 422


class TestFilterValidation:
    """GET /expenses and GET /expenses/totals — invalid category query param."""

    def test_get_expenses_invalid_category_returns_400(self, client):
        """GET /expenses?category=invalid returns 400 with a descriptive message."""
        res = client.get("/expenses", params={"category": "invalid_cat"})

        assert res.status_code == 400
        assert "Invalid category" in res.json()["detail"]

    def test_get_totals_invalid_category_returns_400(self, client):
        """GET /expenses/totals?category=invalid returns 400 with a descriptive message."""
        res = client.get("/expenses/totals", params={"category": "nope"})

        assert res.status_code == 400
        assert "Invalid category" in res.json()["detail"]


class TestDeleteValidation:
    """DELETE /expenses/{id} — error cases."""

    def test_delete_nonexistent_id_returns_404(self, client):
        """DELETE with a non-existent UUID returns 404 with 'Expense not found' detail."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        res = client.delete(f"/expenses/{non_existent_id}")

        assert res.status_code == 404
        assert res.json()["detail"] == "Expense not found"


class TestTotalsEdgeCases:
    """GET /expenses/totals — edge cases."""

    def test_totals_with_no_expenses_returns_zero_and_empty_by_category(self, client):
        """GET /expenses/totals on empty storage returns total=0.0 and empty by_category."""
        res = client.get("/expenses/totals")

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0.0
        assert data["by_category"] == {}


# ===========================================================================
# ADDITIONAL EDGE CASE TESTS
# ===========================================================================


class TestAdditionalEdgeCases:
    """Rounding, aggregation, and case-insensitivity edge cases."""

    def test_amount_rounds_to_two_decimal_places(self, client):
        """Amount 10.999 is stored and returned as 11.0 (rounded to 2 d.p.)."""
        raw_amount = 10.999
        expected_stored = round(raw_amount, 2)  # 11.0

        created = _post_expense(client, amount=raw_amount)

        assert created["amount"] == expected_stored

    def test_totals_correctly_sum_multiple_expenses_across_categories(self, client):
        """Total sum and category breakdown are correct with multiple mixed-category expenses."""
        food_amounts = [12.50, 8.75, 30.00]
        transport_amounts = [5.00, 2.25]

        for amt in food_amounts:
            _post_expense(client, category="food", amount=amt)
        for amt in transport_amounts:
            _post_expense(client, category="transport", amount=amt)

        expected_food_total = round(sum(food_amounts), 2)
        expected_transport_total = round(sum(transport_amounts), 2)
        expected_overall = round(expected_food_total + expected_transport_total, 2)

        res = client.get("/expenses/totals")
        data = res.json()

        assert data["total"] == expected_overall
        assert data["by_category"]["food"] == expected_food_total
        assert data["by_category"]["transport"] == expected_transport_total

    def test_category_filter_is_case_insensitive(self, client):
        """GET /expenses?category=FOOD matches expenses stored with category 'food'."""
        _post_expense(client, title="Burger", category="food")
        _post_expense(client, title="Taxi", category="transport")

        res = client.get("/expenses", params={"category": "FOOD"})

        assert res.status_code == 200
        results = res.json()
        assert len(results) == 1
        assert results[0]["title"] == "Burger"

    def test_multiple_deletes_leave_correct_remaining_expenses(self, client):
        """Deleting some expenses leaves only the un-deleted ones in subsequent GET."""
        exp1 = _post_expense(client, title="Expense A")
        exp2 = _post_expense(client, title="Expense B")
        exp3 = _post_expense(client, title="Expense C")

        client.delete(f"/expenses/{exp1['id']}")
        client.delete(f"/expenses/{exp3['id']}")

        res = client.get("/expenses")
        remaining_ids = {e["id"] for e in res.json()}

        assert remaining_ids == {exp2["id"]}
