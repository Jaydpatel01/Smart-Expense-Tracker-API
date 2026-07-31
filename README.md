# Smart Expense Tracker API

A lightweight REST API to manage, track, filter, and calculate personal expenses built with FastAPI.

## Requirements

- Python 3.11+

## Installation

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Running the Server

```bash
uvicorn src.main:app --reload
```

The API will be running at `http://127.0.0.1:8000`.

### Interactive API Documentation (OpenAPI / Swagger UI)
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Running Tests

```bash
pytest
```
