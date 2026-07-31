"""Unit tests for JSON storage layer in src/storage.py."""

from datetime import date
import json
import os
from pathlib import Path
import pytest

from models import Expense, ExpenseCategory
from storage import ExpenseStorage


@pytest.fixture
def temp_storage(tmp_path):
    """Fixture providing a temporary ExpenseStorage instance."""
    test_file = tmp_path / "expenses_test.json"
    return ExpenseStorage(file_path=test_file)


def test_load_non_existent_file(temp_storage):
    """Test that loading from a non-existent file returns an empty list."""
    assert temp_storage.load() == []


def test_add_and_get_all(temp_storage):
    """Test adding expenses and retrieving them sorted by date descending."""
    exp1 = Expense(
        title="Lunch",
        amount=15.50,
        category=ExpenseCategory.FOOD,
        date="2026-07-20",
    )
    exp2 = Expense(
        title="Dinner",
        amount=45.00,
        category=ExpenseCategory.FOOD,
        date="2026-07-30",
    )
    exp3 = Expense(
        title="Bus Ticket",
        amount=2.50,
        category=ExpenseCategory.TRANSPORT,
        date="2026-07-25",
    )

    temp_storage.add(exp1)
    temp_storage.add(exp2)
    temp_storage.add(exp3)

    all_expenses = temp_storage.get_all()
    assert len(all_expenses) == 3
    # Check descending date order
    assert all_expenses[0].date == "2026-07-30"
    assert all_expenses[1].date == "2026-07-25"
    assert all_expenses[2].date == "2026-07-20"


def test_get_by_id(temp_storage):
    """Test getting expense by unique ID."""
    exp = Expense(
        title="Cinema",
        amount=12.00,
        category=ExpenseCategory.ENTERTAINMENT,
        date="2026-07-28",
    )
    temp_storage.add(exp)

    found = temp_storage.get_by_id(exp.id)
    assert found is not None
    assert found.id == exp.id
    assert found.title == "Cinema"

    missing = temp_storage.get_by_id("non-existent-uuid")
    assert missing is None


def test_delete(temp_storage):
    """Test deleting expense by ID."""
    exp = Expense(
        title="Books",
        amount=30.00,
        category=ExpenseCategory.OTHER,
        date="2026-07-29",
    )
    temp_storage.add(exp)

    assert temp_storage.delete(exp.id) is True
    assert temp_storage.get_by_id(exp.id) is None
    assert temp_storage.delete(exp.id) is False


def test_corrupted_json_raises_runtime_error(temp_storage):
    """Test that malformed JSON raises a RuntimeError."""
    temp_storage.file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_storage.file_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json content ...")

    with pytest.raises(RuntimeError) as exc_info:
        temp_storage.load()
    assert "Failed to read or parse expense data" in str(exc_info.value)


def test_env_var_configuration(monkeypatch, tmp_path):
    """Test that EXPENSE_DATA_PATH environment variable overrides default path."""
    env_file = tmp_path / "env_expenses.json"
    monkeypatch.setenv("EXPENSE_DATA_PATH", str(env_file))
    storage_from_env = ExpenseStorage()
    assert storage_from_env.file_path == env_file
