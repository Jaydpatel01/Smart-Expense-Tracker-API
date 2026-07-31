# AI Notes

This document logs how AI tools were utilized during the development of the Smart Expense Tracker API, detailing generated code, verification steps, and architectural decisions.

## 1. Code Generation Breakdown

- **AI-Generated:** Initial project directory scaffolding, boilerplate FastAPI configuration, Pydantic schemas, and test fixtures.
- **Human-Authored:** Architecture design, file storage isolation for tests, error handling strategies, and boundary validation rules.

## 2. Validation & Verification

- Verified FastAPI routing and Pydantic model serialization.
- Verified test suite execution with isolated JSON file storage to prevent test data leakage into runtime state.

## 3. Rejected Suggestions

- **Database integration (SQLite/PostgreSQL):** Rejected to keep storage dependency minimal via local JSON file per requirements.
- **Multiple optional bonus features:** Kept focus strictly on OpenAPI/Swagger documentation as the single optional bonus item to adhere to submission guidelines.
