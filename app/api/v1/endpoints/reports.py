from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly")
async def monthly_report():
    return {"message": "monthly report endpoint hit ✓", "method": "GET", "path": "/reports/monthly"}


@router.get("/categories")
async def categories_report():
    return {"message": "categories report endpoint hit ✓", "method": "GET", "path": "/reports/categories"}


@router.get("/cashflow")
async def cashflow_report():
    return {"message": "cashflow report endpoint hit ✓", "method": "GET", "path": "/reports/cashflow"}

