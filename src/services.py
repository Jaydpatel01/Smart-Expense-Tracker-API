"""Business logic layer for expense calculations, filtering, and summaries."""

from typing import List, Optional

try:
    from .models import Expense, ExpenseCreate, TotalResponse
    from .storage import ExpenseStorage, storage
except (ImportError, ValueError):
    from models import Expense, ExpenseCreate, TotalResponse
    from storage import ExpenseStorage, storage


def create_expense(
    data: ExpenseCreate, target_storage: Optional[ExpenseStorage] = None
) -> Expense:
    """Create and persist a new expense object.

    Args:
        data: Input validation schema containing title, amount, category, date.
        target_storage: Optional storage instance (defaults to module singleton).

    Returns:
        The newly created Expense object with generated UUID and UTC created_at timestamp.
    """
    store = target_storage or storage
    expense = Expense(**data.model_dump())
    return store.add(expense)


def get_expenses(
    category: Optional[str] = None, target_storage: Optional[ExpenseStorage] = None
) -> List[Expense]:
    """Retrieve all expenses, optionally filtered by category.

    Args:
        category: Optional category filter string (case-insensitive).
        target_storage: Optional storage instance (defaults to module singleton).

    Returns:
        List of Expense objects sorted by date descending.
    """
    store = target_storage or storage
    expenses = store.get_all()

    if not category:
        return expenses

    category_lower = category.strip().lower()
    filtered = [
        e
        for e in expenses
        if str(
            e.category.value if hasattr(e.category, "value") else e.category
        ).lower()
        == category_lower
    ]
    return sorted(filtered, key=lambda e: e.date, reverse=True)


def calculate_totals(
    category: Optional[str] = None, target_storage: Optional[ExpenseStorage] = None
) -> TotalResponse:
    """Calculate overall expense total and category breakdowns.

    Args:
        category: Optional category string to filter total calculation.
        target_storage: Optional storage instance (defaults to module singleton).

    Returns:
        TotalResponse containing overall total and category breakdown dictionary.
    """
    store = target_storage or storage
    expenses = store.get_all()

    if category:
        cat_clean = category.strip().lower()
        matching_expenses = [
            e
            for e in expenses
            if str(
                e.category.value if hasattr(e.category, "value") else e.category
            ).lower()
            == cat_clean
        ]
        cat_total = round(sum(e.amount for e in matching_expenses), 2)
        return TotalResponse(total=cat_total, by_category={cat_clean: cat_total})

    overall_total = round(sum(e.amount for e in expenses), 2)
    by_category: dict[str, float] = {}
    for e in expenses:
        cat_name = str(
            e.category.value if hasattr(e.category, "value") else e.category
        ).lower()
        # Round after each addition rather than at the end only — floating-point
        # representation errors accumulate across multiple additions (e.g.
        # 12.50 + 8.75 + 30.00 can produce 50.99999... without per-step rounding).
        by_category[cat_name] = round(by_category.get(cat_name, 0.0) + e.amount, 2)

    return TotalResponse(total=overall_total, by_category=by_category)


def delete_expense(
    expense_id: str, target_storage: Optional[ExpenseStorage] = None
) -> bool:
    """Delete an expense by unique ID.

    Args:
        expense_id: UUID string of the expense to delete.
        target_storage: Optional storage instance (defaults to module singleton).

    Returns:
        True if deleted successfully, False if expense ID was not found.
    """
    store = target_storage or storage
    return store.delete(expense_id)
