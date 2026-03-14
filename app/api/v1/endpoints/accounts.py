from fastapi import APIRouter
from app.schemas.account import (
    AccountCreate,
    AccountUpdate,
    AccountRead,
    BalanceResponse,
)

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountRead])
async def list_accounts():
    return []


@router.post("", response_model=AccountRead, status_code=201)
async def create_account(data: AccountCreate):
    return {
        "id": 1,
        "name": data.name,
        "type": data.type,
        "currency": data.currency,
        "owner_id": 1,
    }


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(account_id: int):
    return {
        "id": account_id,
        "name": "Main Checking",
        "type": "checking",
        "currency": "USD",
        "owner_id": 1,
    }


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(account_id: int, data: AccountUpdate):
    return {
        "id": account_id,
        "name": data.name or "Main Checking",
        "type": "checking",
        "currency": data.currency or "USD",
        "owner_id": 1,
    }


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int):
    return None


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(account_id: int):
    return {
        "account_id": account_id,
        "account_name": "Main Checking",
        "currency": "USD",
        "balance": "1500.00",
    }
