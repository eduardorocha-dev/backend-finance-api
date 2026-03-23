from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="FinTrack API",
    description="""
Personal Finance Tracker REST API.

> 🚧 Endpoints are still returning **stub responses** — repositories and services are not yet implemented.
> The database layer (models, migrations) is fully set up and connected.

## Status

- **Models** — all 6 models defined and migrated to PostgreSQL
- **Schemas** — all request/response schemas defined
- **Endpoints** — routes exist, returning stub data

## Endpoints

- **Auth** — register, login, get current user
- **Accounts** — manage financial accounts
- **Transactions** — income, expenses, transfers
- **Categories** — organize transactions
- **Budgets** — monthly spending limits
- **Reports** — aggregated financial insights
- **Exports** — async CSV / PDF generation
    """,
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["General"])
async def health():
    """Check the API is running."""
    return {"status": "ok", "version": "0.1.0"}
