from fastapi import APIRouter
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetRead, BudgetUsage

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetRead])
async def list_budgets():
    return []


@router.post("", response_model=BudgetRead, status_code=201)
async def create_budget(data: BudgetCreate):
    return {
        "id": 1,
        "category_id": data.category_id,
        "limit_amount": data.limit_amount,
        "month": data.month,
        "owner_id": 1,
    }


@router.get("/usage", response_model=list[BudgetUsage])
async def get_usage():
    return []


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(budget_id: int):
    return {
        "id": budget_id,
        "category_id": 1,
        "limit_amount": "500.00",
        "month": "2024-03-01",
        "owner_id": 1,
    }


@router.patch("/{budget_id}", response_model=BudgetRead)
async def update_budget(budget_id: int, data: BudgetUpdate):
    return {
        "id": budget_id,
        "category_id": 1,
        "limit_amount": data.limit_amount or "500.00",
        "month": "2024-03-01",
        "owner_id": 1,
    }


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: int):
    return None
