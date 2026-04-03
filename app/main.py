from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="FinTrack API",
    description="""
Production-grade personal finance tracker REST API built with FastAPI, PostgreSQL, Redis, and Celery.

## Endpoints

- **Auth** — register, login, refresh token, get current user
- **Accounts** — manage financial accounts (checking, savings, credit card, cash)
- **Transactions** — immutable ledger with soft-delete and correction entries
- **Categories** — user-defined categories with parent support
- **Budgets** — monthly spending limits with usage tracking and alert thresholds
- **Reports** — monthly summaries, category breakdowns, and cash flow
- **Exports** — async CSV / PDF generation via background workers
    """,
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["General"])
async def health():
    """Check the API is running."""
    return {"status": "ok", "version": "1.0.0"}
