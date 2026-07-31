# AI Notes

This document records how AI tools were used during development of the Smart Expense Tracker API — specifically which parts were generated, what I validated or changed, and where I overrode the AI's suggestions and why.

---

## 1. Which parts were AI-generated vs. written by me

**AI-generated (then reviewed and kept):**
- Initial file/folder scaffold: `src/`, `tests/`, `requirements.txt`, `.gitignore`
- FastAPI app entry point boilerplate in `src/main.py` (the `FastAPI(...)` call, router inclusion, and root endpoint)
- The `ExpenseStorage` class skeleton in `src/storage.py` — method signatures and the basic read/write pattern
- The `conftest.py` `async_client` fixture using `httpx.AsyncClient` with `ASGITransport`
- The `@field_validator` decorators on `ExpenseBase` for `title`, `amount`, and `date`

**Written or substantially rewritten by me:**
- The future-date check in `validate_date`: the AI's initial validator only checked that the date string matched `YYYY-MM-DD` format. It accepted `date: "2099-01-01"` without error. I manually tested `POST /expenses` with that payload and confirmed it created an expense in the future. That's wrong business logic, so I added the `if parsed_date > date.today()` guard myself.
- The atomic write pattern in `storage.save()`: the AI generated a plain `json.dump(data, file)` — no temp file, no fsync. I replaced it with write-to-temp-then-`os.replace()` because a plain write can leave a truncated file if the process is killed mid-write. I verified this matters by terminating the server with Ctrl+C during a POST and confirming the file survived intact.
- The `EXPENSE_DATA_PATH` environment variable and per-test storage isolation: the AI's first fixture version didn't isolate state between tests. Test B was seeing expenses created by test A because they shared `data/expenses.json`. I fixed it by monkeypatching both the env var and `storage_module.storage.file_path` on the singleton directly, pointing each test to a fresh `tmp_path` file.
- The `target_storage` parameter on every service function: the AI wrote service functions that called the module-level `storage` singleton directly. There was no way to inject a different store for unit tests. I refactored every function to accept an optional `target_storage` argument so unit tests could pass an isolated instance without touching the file system.
- The `src/` layout import resolution: the AI initially used flat imports (`from models import ...`) everywhere. These worked when `src` was on `sys.path` but broke when `uvicorn src.main:app` imported `src` as a package. I switched internal `src/` modules to relative imports with a `try/except` fallback so the code works in both execution contexts.

---

## 2. What I validated, tested, or changed in the AI's output — and why

**Date validator — future-date check:**
The AI generated a validator that called `date.fromisoformat(v)` and raised on parse failure, but returned the string without checking whether it was in the future. I caught this by testing `POST /expenses` with `"date": "2099-01-01"` and seeing a 201 response. I added `if parsed_date > date.today(): raise ValueError("Date cannot be in the future")` and added `test_expense_create_future_date` to the test suite to lock in the correct behaviour.

**HTTP status code for invalid category query param:**
The AI initially returned `422 Unprocessable Entity` when `GET /expenses?category=invalid` was called. I changed it to `400 Bad Request`. The reason: 422 is the correct code when Pydantic fails to parse a request *body* — it signals schema validation failure. A query parameter that's syntactically valid but semantically wrong is a routing-level client error, which maps to 400. The distinction matters for clients that branch on status code.

**Separate input and response models:**
The AI generated a single `Expense` model used for both input and output. I separated them into `ExpenseCreate` (input — no `id`, no `created_at`) and `ExpenseResponse` (output — full record). This is the right design because the two concerns evolve independently: you might add fields to responses (e.g. `updated_at`, computed tags) without changing what clients send. Conflating them creates coupling that breaks when the API grows.

**Timezone-aware timestamps:**
The AI's initial `Expense` model used `datetime.utcnow()` for `created_at`, which returns a naive datetime with no timezone info. Comparing or serialising naive datetimes causes bugs in downstream systems. I changed it to `datetime.now(timezone.utc)`, which returns a timezone-aware object. FastAPI serialises this correctly to ISO 8601 with a `Z` suffix.

**Test isolation — fixture rewrite:**
The AI's first `conftest.py` used `@pytest.fixture` (synchronous) on an `async def` function, which pytest silently skipped. The `test_health_check` test was marked as skipped in early runs with a `PytestUnhandledCoroutineWarning`. I changed the decorator to `@pytest_asyncio.fixture` and confirmed all async tests ran correctly. I then rewrote the `client` fixture three times before it properly isolated state: version one shared the singleton, version two patched the env var but not the singleton's already-resolved path, and version three patched both, which is what's in the final file.

**Amount rounding in totals:**
The AI's `calculate_totals` implementation summed amounts but applied `round()` only to the final total, not to individual category subtotals accumulated in a loop. With floating-point arithmetic, `12.50 + 8.75 + 30.00` can accumulate representation error. I changed it to `round(by_category.get(cat_name, 0.0) + e.amount, 2)` at each step, which keeps subtotals clean and avoids a `65.49999...` where the test expects `65.50`.

---

## 3. AI suggestions I decided not to use — and why

**SQLite for storage:**
The AI suggested using SQLite with SQLAlchemy after I asked about persistence options. I rejected it. The spec says "no database required" — SQLite is a database engine (it has a query planner, transactions, and ACID guarantees). Using it would solve a problem the spec didn't ask me to solve and introduce a dependency I don't need. A plain JSON file with atomic writes is correct here.

**Returning 422 for invalid category query params:**
Explained above in Section 2. The AI's position was that `category` could be modelled as an enum query parameter in FastAPI, which would produce automatic 422 validation. I chose to handle it manually with a helper function and return 400 because query parameter validation is semantically different from request body schema validation.

**Using a single `Expense` model for input and output:**
The AI proposed simplifying the schema by dropping `ExpenseCreate` and using `Expense` directly in `POST /expenses`, with `id` and `created_at` as optional fields. I rejected this because it would expose `id` and `created_at` as writable fields in the OpenAPI schema — clients could send arbitrary UUIDs and timestamps, bypassing server-side generation entirely. Separating input and output models removes that surface entirely.

**`datetime.utcnow()` for timestamps:**
The AI used `datetime.utcnow()`. I rejected it in favour of `datetime.now(timezone.utc)`. `utcnow()` is deprecated in Python 3.12+ precisely because it creates naive datetimes that have no timezone context. Using it would produce correct values but incorrect type semantics.

**Flat imports throughout `src/`:**
The AI used `from models import ...` in every `src/` file. This works when `src` is added to `sys.path` (as pytest does via `pythonpath`), but breaks when uvicorn imports `src.main` as a package because relative imports are required in that context. I switched to relative imports (`from .models import ...`) with a `try/except` fallback to bare names, so the code works correctly in both execution contexts without requiring `PYTHONPATH` manipulation.

**Docker support as the bonus feature:**
The AI suggested adding a `Dockerfile` as the optional bonus. I chose OpenAPI/Swagger docs instead. FastAPI generates these automatically at `/docs` and `/redoc` with zero extra dependencies — the bonus costs nothing and adds real interactive value to reviewers who want to explore the API without writing curl commands. Docker would have added a file to maintain and a build step to document, for no functional benefit over `uvicorn`.
