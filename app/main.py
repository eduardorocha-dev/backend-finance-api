from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="FinTrack API",
    description="""
Personal Finance Tracker REST API.

> 🚧 Currently running with **stub endpoints** — no database connected yet.
> Every endpoint returns a confirmation message so you can verify paths and methods are correct.

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

