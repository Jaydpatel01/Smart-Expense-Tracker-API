# Smart Expense Tracker API

A REST API for managing personal expenses, built with FastAPI and persistent JSON file storage.

---

## Features

- Add an expense with title, amount, category, and date
- View all expenses, sorted by date descending
- Filter expenses by category
- Calculate total expenses — overall and broken down by category
- Delete an expense by ID
- Interactive API documentation via OpenAPI / Swagger UI (bonus)

---

## Requirements

- Python 3.11 or higher

---

## Installation

```bash
git clone <repo>
cd <repo>
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the Server

```bash
uvicorn src.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

---

## Running Tests

```bash
pytest tests/ -v
```

---

## API Endpoints

| Method   | Path                    | Description                                      | Example                                      |
|----------|-------------------------|--------------------------------------------------|----------------------------------------------|
| `POST`   | `/expenses`             | Add a new expense                                | `POST /expenses` with JSON body              |
| `GET`    | `/expenses`             | View all expenses                                | `GET /expenses`                              |
| `GET`    | `/expenses?category=`   | Filter expenses by category                      | `GET /expenses?category=food`                |
| `GET`    | `/expenses/totals`      | Get total expenses overall and by category       | `GET /expenses/totals`                       |
| `GET`    | `/expenses/totals?category=` | Get total for a specific category           | `GET /expenses/totals?category=transport`    |
| `DELETE` | `/expenses/{id}`        | Delete an expense by its ID                      | `DELETE /expenses/3fa85f64-...`              |

### Request Body — POST /expenses

```json
{
  "title": "Grocery run",
  "amount": 47.50,
  "category": "food",
  "date": "2026-07-31"
}
```

Allowed categories: `food`, `transport`, `housing`, `entertainment`, `health`, `shopping`, `other`.

### Response — POST /expenses (201 Created)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Grocery run",
  "amount": 47.50,
  "category": "food",
  "date": "2026-07-31",
  "created_at": "2026-07-31T14:00:00.000000Z"
}
```

---

## API Documentation

Interactive documentation is automatically generated and available once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Data Storage

Expenses are stored in a local JSON file at `data/expenses.json`. This directory and file are created automatically on the first write — no setup is required.

To use a different storage path (e.g. for testing), set the `EXPENSE_DATA_PATH` environment variable:

```bash
EXPENSE_DATA_PATH=/tmp/my_expenses.json uvicorn src.main:app --reload
```

---

## Design Decisions

- **FastAPI over Flask**: FastAPI provides automatic request validation via Pydantic, native async support, and generates OpenAPI documentation out of the box — all without additional configuration.
- **JSON file storage**: Satisfies the no-database requirement while demonstrating file I/O, atomic writes (write-then-rename), and correct serialisation of complex types. The `EXPENSE_DATA_PATH` environment variable decouples the storage path from the application, which keeps tests fully isolated.
- **Layered architecture**: The codebase is split into `models` (Pydantic schemas), `storage` (file I/O), `services` (business logic), and `routers` (HTTP layer). Each layer has a single responsibility, making the code straightforward to test and extend independently.
- **Pydantic v2 validation**: All input validation — including amount rounding, date format checking, future-date rejection, and whitespace trimming — is declared in the model layer and enforced automatically before any business logic runs.
