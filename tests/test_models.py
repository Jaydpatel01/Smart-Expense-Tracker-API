"""Unit tests for Pydantic models in src/models.py."""

from datetime import date, timedelta
import pytest
from pydantic import ValidationError

from src.models import ExpenseCategory, ExpenseCreate, Expense, TotalResponse


def test_expense_create_valid():
    """Test valid ExpenseCreate schema instantiation."""
    data = {
        "title": "  Grocery Shopping  ",
        "amount": 45.678,
        "category": "food",
        "date": date.today().isoformat(),
    }
    expense_in = ExpenseCreate(**data)
    assert expense_in.title == "Grocery Shopping"
    assert expense_in.amount == 45.68
    assert expense_in.category == ExpenseCategory.FOOD
    assert expense_in.date == date.today().isoformat()


def test_expense_create_empty_title():
    """Test that empty or whitespace title raises ValidationError."""
    data = {
        "title": "   ",
        "amount": 10.0,
        "category": "food",
        "date": date.today().isoformat(),
    }
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(**data)
    assert "Title must not be empty or whitespace only" in str(exc_info.value)


def test_expense_create_invalid_amount():
    """Test that zero or negative amount raises ValidationError."""
    data = {
        "title": "Coffee",
        "amount": -5.0,
        "category": "food",
        "date": date.today().isoformat(),
    }
    with pytest.raises(ValidationError):
        ExpenseCreate(**data)


def test_expense_create_future_date():
    """Test that future date raises ValidationError."""
    future_date = (date.today() + timedelta(days=1)).isoformat()
    data = {
        "title": "Future Subscription",
        "amount": 15.0,
        "category": "entertainment",
        "date": future_date,
    }
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(**data)
    assert "Date cannot be in the future" in str(exc_info.value)


def test_expense_create_invalid_date_format():
    """Test that invalid date format raises ValidationError."""
    data = {
        "title": "Dinner",
        "amount": 30.0,
        "category": "food",
        "date": "31-07-2026",
    }
    with pytest.raises(ValidationError) as exc_info:
        ExpenseCreate(**data)
    assert "Date must be a valid ISO 8601 string" in str(exc_info.value)


def test_expense_full_model_defaults():
    """Test that Expense model generates UUID id and UTC created_at timestamp."""
    data = {
        "title": "Rent",
        "amount": 1200.0,
        "category": "housing",
        "date": date.today().isoformat(),
    }
    expense = Expense(**data)
    assert expense.id is not None
    assert len(expense.id) == 36  # UUID v4 string length
    assert expense.created_at is not None


def test_total_response_model():
    """Test TotalResponse schema."""
    resp = TotalResponse(total=100.5, by_category={"food": 50.25, "transport": 50.25})
    assert resp.total == 100.5
    assert resp.by_category["food"] == 50.25
