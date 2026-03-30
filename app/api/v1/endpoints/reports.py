from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import CashFlowResponse, CategoryBreakdownResponse, MonthlySummary
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly", response_model=MonthlySummary)
async def monthly_report(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    month: date = Query(..., examples="2024-03-01"),
):
    return await ReportService(session).monthly(current_user.id, month)


@router.get("/categories", response_model=CategoryBreakdownResponse)
async def categories_report(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    month: date = Query(..., examples="2024-03-01"),
):
    return await ReportService(session).category_breakdown(current_user.id, month)


@router.get("/cashflow", response_model=CashFlowResponse)
async def cashflow_report(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    date_from: date = Query(..., examples="2024-03-01"),
    date_to: date = Query(..., examples="2024-03-31"),
):
    return await ReportService(session).cashflow(current_user.id, date_from, date_to)
