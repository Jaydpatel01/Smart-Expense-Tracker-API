"""Unit tests for business logic in src/services.py."""

from datetime import date
import pytest

from models import ExpenseCategory, ExpenseCreate
from services import (
    calculate_totals,
    create_expense,
    delete_expense,
    get_expenses,
)
from storage import ExpenseStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Fixture providing a temporary ExpenseStorage instance."""
    test_file = tmp_path / "services_test_expenses.json"
    return ExpenseStorage(file_path=test_file)


def test_create_expense(temp_storage):
    """Test expense creation with UUID generation and storage delegate."""
    data = ExpenseCreate(
        title="Supermarket",
        amount=55.40,
        category=ExpenseCategory.FOOD,
        date="2026-07-25",
    )
    created = create_expense(data, target_storage=temp_storage)

    assert created.id is not None
    assert len(created.id) == 36
    assert created.title == "Supermarket"
    assert created.amount == 55.40
    assert temp_storage.get_by_id(created.id) is not None


def test_get_expenses_unfiltered_and_filtered(temp_storage):
    """Test retrieving expenses with and without category filtering (case-insensitive)."""
    exp1 = ExpenseCreate(
        title="Lunch", amount=12.00, category=ExpenseCategory.FOOD, date="2026-07-20"
    )
    exp2 = ExpenseCreate(
        title="Taxi",
        amount=25.50,
        category=ExpenseCategory.TRANSPORT,
        date="2026-07-30",
    )
    exp3 = ExpenseCreate(
        title="Dinner", amount=40.00, category=ExpenseCategory.FOOD, date="2026-07-28"
    )

    create_expense(exp1, target_storage=temp_storage)
    create_expense(exp2, target_storage=temp_storage)
    create_expense(exp3, target_storage=temp_storage)

    # All expenses sorted by date descending
    all_expenses = get_expenses(target_storage=temp_storage)
    assert len(all_expenses) == 3
    assert all_expenses[0].title == "Taxi"  # 2026-07-30

    # Filter by category case-insensitively
    food_expenses = get_expenses(category="FOOD", target_storage=temp_storage)
    assert len(food_expenses) == 2
    assert food_expenses[0].title == "Dinner"  # 2026-07-28
    assert food_expenses[1].title == "Lunch"  # 2026-07-20


def test_calculate_totals_overall_and_category(temp_storage):
    """Test calculate_totals overall sum and category breakdown."""
    create_expense(
        ExpenseCreate(
            title="Groceries",
            amount=50.25,
            category=ExpenseCategory.FOOD,
            date="2026-07-20",
        ),
        target_storage=temp_storage,
    )
    create_expense(
        ExpenseCreate(
            title="Metro",
            amount=10.50,
            category=ExpenseCategory.TRANSPORT,
            date="2026-07-21",
        ),
        target_storage=temp_storage,
    )
    create_expense(
        ExpenseCreate(
            title="Snacks",
            amount=15.25,
            category=ExpenseCategory.FOOD,
            date="2026-07-22",
        ),
        target_storage=temp_storage,
    )

    # Overall totals
    totals = calculate_totals(target_storage=temp_storage)
    assert totals.total == 76.00
    assert totals.by_category["food"] == 65.50
    assert totals.by_category["transport"] == 10.50

    # Single category total
    food_totals = calculate_totals(category="food", target_storage=temp_storage)
    assert food_totals.total == 65.50
    assert food_totals.by_category == {"food": 65.50}


def test_calculate_totals_empty(temp_storage):
    """Test calculate_totals when no expenses exist or category has no matches."""
    empty_totals = calculate_totals(target_storage=temp_storage)
    assert empty_totals.total == 0.0
    assert empty_totals.by_category == {}

    missing_cat_totals = calculate_totals(
        category="health", target_storage=temp_storage
    )
    assert missing_cat_totals.total == 0.0
    assert missing_cat_totals.by_category == {"health": 0.0}


def test_delete_expense(temp_storage):
    """Test deleting expense through service layer."""
    exp = create_expense(
        ExpenseCreate(
            title="Movie",
            amount=15.00,
            category=ExpenseCategory.ENTERTAINMENT,
            date="2026-07-25",
        ),
        target_storage=temp_storage,
    )

    assert delete_expense(exp.id, target_storage=temp_storage) is True
    assert delete_expense(exp.id, target_storage=temp_storage) is False
