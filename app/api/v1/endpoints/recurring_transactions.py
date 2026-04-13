from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.recurring_transaction import (
    RecurringTransactionCreate,
    RecurringTransactionRead,
    RecurringTransactionUpdate,
)
from app.services.recurring_transaction import RecurringTransactionService

router = APIRouter(prefix="/recurring-transactions", tags=["Recurring Transactions"])


@router.get("", response_model=list[RecurringTransactionRead])
async def list_recurring(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await RecurringTransactionService(session).list(current_user.id)


@router.post("", response_model=RecurringTransactionRead, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    data: RecurringTransactionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    rt = await RecurringTransactionService(session).create(current_user.id, data)
    await session.commit()
    return rt


@router.get("/{recurring_id}", response_model=RecurringTransactionRead)
async def get_recurring(
    recurring_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await RecurringTransactionService(session).get(current_user.id, recurring_id)


@router.patch("/{recurring_id}", response_model=RecurringTransactionRead)
async def update_recurring(
    recurring_id: int,
    data: RecurringTransactionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    rt = await RecurringTransactionService(session).update(current_user.id, recurring_id, data)
    await session.commit()
    return rt


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    recurring_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await RecurringTransactionService(session).delete(current_user.id, recurring_id)
    await session.commit()
