"""Data models and schemas for expense tracking using Pydantic."""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Dict
import uuid

from pydantic import BaseModel, Field, field_validator


class ExpenseCategory(str, Enum):
    """Allowed categories for expenses."""

    FOOD = "food"
    TRANSPORT = "transport"
    HOUSING = "housing"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    SHOPPING = "shopping"
    OTHER = "other"


class ExpenseBase(BaseModel):
    """Base model containing shared expense attributes and validators."""

    title: str = Field(
        ..., max_length=100, description="Expense title (max 100 characters)"
    )
    amount: float = Field(..., gt=0, description="Expense amount (must be > 0)")
    category: ExpenseCategory = Field(..., description="Allowed expense category")
    date: str = Field(
        ..., description="Expense date in ISO 8601 format (YYYY-MM-DD)"
    )

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Strip leading/trailing whitespace and ensure title is not empty."""
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title must not be empty or whitespace only")
        return stripped

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Ensure amount is strictly greater than zero and rounded to 2 decimal places."""
        if v <= 0:
            raise ValueError("Amount must be strictly greater than 0")
        return round(v, 2)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate that date is a valid YYYY-MM-DD ISO 8601 string and not in the future."""
        try:
            parsed_date = date.fromisoformat(v)
        except ValueError:
            raise ValueError(
                "Date must be a valid ISO 8601 string in YYYY-MM-DD format"
            )

        today = date.today()
        if parsed_date > today:
            raise ValueError("Date cannot be in the future")

        return parsed_date.isoformat()


class ExpenseCreate(ExpenseBase):
    """Input schema for creating a new expense."""

    pass


class Expense(ExpenseBase):
    """Full domain model representing a stored expense with unique ID and creation timestamp."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUIDv4 identifier",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the expense was created (UTC)",
    )


class ExpenseResponse(Expense):
    """API response schema for an expense object."""

    pass


class TotalResponse(BaseModel):
    """API response schema for total expenses and category breakdowns."""

    total: float = Field(
        ..., description="Overall total expense amount rounded to 2 decimal places"
    )
    by_category: Dict[str, float] = Field(
        ..., description="Expenses total grouped by category"
    )
