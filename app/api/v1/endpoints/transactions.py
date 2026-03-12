from fastapi import APIRouter

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("")
async def list_transactions():
    return {"message": "list transactions endpoint hit ✓", "method": "GET", "path": "/transactions"}


@router.post("", status_code=201)
async def create_transaction():
    return {"message": "create transaction endpoint hit ✓", "method": "POST", "path": "/transactions"}


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int):
    return {"message": "get transaction endpoint hit ✓", "method": "GET", "path": f"/transactions/{transaction_id}", "transaction_id": transaction_id}


@router.patch("/{transaction_id}")
async def update_transaction(transaction_id: int):
    return {"message": "update transaction endpoint hit ✓", "method": "PATCH", "path": f"/transactions/{transaction_id}", "transaction_id": transaction_id}


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int):
    return None
