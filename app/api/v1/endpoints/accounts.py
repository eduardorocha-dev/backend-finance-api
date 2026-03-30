from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate, BalanceResponse
from app.services.account import AccountService

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountRead])
async def list_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await AccountService(session).list(current_user.id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    account = await AccountService(session).create(current_user.id, data)
    await session.commit()
    return account


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await AccountService(session).get(current_user.id, account_id)


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    account = await AccountService(session).update(current_user.id, account_id, data)
    await session.commit()
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await AccountService(session).delete(current_user.id, account_id)
    await session.commit()


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(
    account_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await AccountService(session).get_balance(current_user.id, account_id)
