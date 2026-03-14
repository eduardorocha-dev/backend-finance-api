from datetime import date
from fastapi import APIRouter, Query
from app.schemas.report import (
    MonthlySummary,
    CategoryBreakdownResponse,
    CashFlowResponse,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly", response_model=MonthlySummary)
async def monthly_report(month: date = Query(..., examples="2024-03-01")):
    return {
        "month": month,
        "total_income": "0.00",
        "total_expenses": "0.00",
        "net": "0.00",
    }


@router.get("/categories", response_model=CategoryBreakdownResponse)
async def categories_report(month: date = Query(..., examples="2024-03-01")):
    return {
        "month": month,
        "total_expenses": "0.00",
        "breakdown": [],
    }


@router.get("/cashflow", response_model=CashFlowResponse)
async def cashflow_report(
    date_from: date = Query(..., examples="2024-03-01"),
    date_to: date = Query(..., examples="2024-03-31"),
):
    return {
        "date_from": date_from,
        "date_to": date_to,
        "entries": [],
    }
