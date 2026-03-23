from fastapi import APIRouter

from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionRead])
async def list_transactions():
    return []


@router.post("", response_model=TransactionRead, status_code=201)
async def create_transaction(data: TransactionCreate):
    return {
        "id": 1,
        "account_id": data.account_id,
        "category_id": data.category_id,
        "type": data.type,
        "amount": data.amount,
        "description": data.description,
        "date": data.date,
        "is_deleted": False,
        "created_at": data.date,
    }


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(transaction_id: int):
    return {
        "id": transaction_id,
        "account_id": 1,
        "category_id": 1,
        "type": "expense",
        "amount": "50.00",
        "description": "Groceries",
        "date": "2024-03-01T00:00:00",
        "is_deleted": False,
        "created_at": "2024-03-01T00:00:00",
    }


@router.patch("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(transaction_id: int, data: TransactionUpdate):
    return {
        "id": transaction_id,
        "account_id": 1,
        "category_id": data.category_id or 1,
        "type": "expense",
        "amount": "50.00",
        "description": data.description,
        "date": "2024-03-01T00:00:00",
        "is_deleted": False,
        "created_at": "2024-03-01T00:00:00",
    }


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int):
    return None
