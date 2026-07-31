"""API route handlers for managing expenses."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status

from models import ExpenseCategory, ExpenseCreate, ExpenseResponse, TotalResponse
from services import (
    calculate_totals,
    create_expense,
    delete_expense,
    get_expenses,
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])

ALLOWED_CATEGORIES = {c.value for c in ExpenseCategory}


def _validate_category(category: Optional[str]) -> None:
    """Validate that category parameter is one of the allowed categories."""
    if category is not None:
        cat_clean = category.strip().lower()
        if cat_clean not in ALLOWED_CATEGORIES:
            allowed_str = ", ".join([c.value for c in ExpenseCategory])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {allowed_str}",
            )


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new expense",
    description="Create and persist a new expense entry with title, amount, category, and date.",
)
@router.post(
    "/",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_expense_endpoint(expense_in: ExpenseCreate) -> ExpenseResponse:
    """Endpoint to add a new expense."""
    return create_expense(expense_in)


@router.get(
    "",
    response_model=List[ExpenseResponse],
    summary="View all expenses",
    description="Retrieve all expenses sorted by date descending, optionally filtered by category.",
)
@router.get(
    "/",
    response_model=List[ExpenseResponse],
    include_in_schema=False,
)
async def get_expenses_endpoint(
    category: Optional[str] = Query(None, description="Filter expenses by category")
) -> List[ExpenseResponse]:
    """Endpoint to retrieve expenses with optional category filtering."""
    _validate_category(category)
    return get_expenses(category=category)


@router.get(
    "/totals",
    response_model=TotalResponse,
    summary="Calculate total expenses",
    description="Calculate overall expense total and breakdown by category, or total for a specific category.",
)
async def get_totals_endpoint(
    category: Optional[str] = Query(
        None, description="Calculate totals for a specific category"
    )
) -> TotalResponse:
    """Endpoint to calculate total expenses and category breakdowns."""
    _validate_category(category)
    return calculate_totals(category=category)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
    description="Remove an existing expense by its unique UUID string.",
)
async def delete_expense_endpoint(expense_id: str) -> Response:
    """Endpoint to delete an expense by ID."""
    deleted = delete_expense(expense_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
