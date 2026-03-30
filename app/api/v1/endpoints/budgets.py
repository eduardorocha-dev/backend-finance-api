from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate, BudgetUsage
from app.services.budget import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=list[BudgetRead])
async def list_budgets(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    month: date | None = Query(None, examples="2024-03-01"),
):
    return await BudgetService(session).list(current_user.id, month)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    budget = await BudgetService(session).create(current_user.id, data)
    await session.commit()
    return budget


@router.get("/usage", response_model=list[BudgetUsage])
async def get_usage(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    month: date = Query(..., examples="2024-03-01"),
):
    return await BudgetService(session).get_usage(current_user.id, month)


@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await BudgetService(session).get(current_user.id, budget_id)


@router.patch("/{budget_id}", response_model=BudgetRead)
async def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    budget = await BudgetService(session).update(current_user.id, budget_id, data)
    await session.commit()
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await BudgetService(session).delete(current_user.id, budget_id)
    await session.commit()
