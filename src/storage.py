"""JSON file storage and persistence logic for managing expenses."""

import json
import os
from pathlib import Path
from typing import List, Optional
import uuid

from models import Expense


class ExpenseStorage:
    """JSON file storage manager for persisting expenses safely and atomically."""

    def __init__(self, file_path: Optional[Path | str] = None):
        """Initialize storage with an explicit path or fallback to EXPENSE_DATA_PATH / default."""
        if file_path:
            self.file_path = Path(file_path)
        else:
            env_path = os.getenv("EXPENSE_DATA_PATH", "data/expenses.json")
            self.file_path = Path(env_path)

    def load(self) -> List[Expense]:
        """Read and deserialize all expenses from the JSON file.

        Returns an empty list if the file does not exist. Raises RuntimeError if corrupt.
        """
        if not self.file_path.exists():
            return []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                raw_data = json.loads(content)
                if not isinstance(raw_data, list):
                    raise ValueError("JSON content must be a list of expense objects")
                return [Expense(**item) for item in raw_data]
        except Exception as e:
            raise RuntimeError(
                f"Failed to read or parse expense data from '{self.file_path}': {e}"
            ) from e

    def save(self, expenses: List[Expense]) -> None:
        """Serialize and write all expenses atomically to the JSON file using a temp file and rename."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        serialized_data = [e.model_dump(mode="json") for e in expenses]

        temp_file = self.file_path.with_name(
            f".tmp_{uuid.uuid4().hex}_{self.file_path.name}"
        )
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(serialized_data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            temp_file.replace(self.file_path)
        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise RuntimeError(f"Failed to save expense data: {e}") from e

    def add(self, expense: Expense) -> Expense:
        """Load current expenses, append new expense, save atomically, and return the expense."""
        expenses = self.load()
        expenses.append(expense)
        self.save(expenses)
        return expense

    def get_all(self) -> List[Expense]:
        """Return all expenses sorted by date descending."""
        expenses = self.load()
        return sorted(expenses, key=lambda e: e.date, reverse=True)

    def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Retrieve an expense by its unique identifier. Return None if not found."""
        expenses = self.load()
        for expense in expenses:
            if expense.id == expense_id:
                return expense
        return None

    def delete(self, expense_id: str) -> bool:
        """Delete an expense by its unique identifier. Return True if deleted, False if not found."""
        expenses = self.load()
        initial_len = len(expenses)
        updated_expenses = [e for e in expenses if e.id != expense_id]
        if len(updated_expenses) == initial_len:
            return False

        self.save(updated_expenses)
        return True


# Module-level singleton instance
storage = ExpenseStorage()
