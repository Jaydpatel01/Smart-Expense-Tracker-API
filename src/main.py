"""FastAPI application entry point and configuration."""

from fastapi import FastAPI

try:
    from .routers import expenses
except (ImportError, ValueError):
    from routers import expenses

app = FastAPI(
    title="Smart Expense Tracker API",
    description="A lightweight REST API to manage, track, filter, and calculate personal expenses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include route handlers
app.include_router(expenses.router)


@app.get("/", tags=["Health"])
async def root():
    """Health check / root endpoint."""
    return {"status": "ok", "message": "Smart Expense Tracker API is running"}
