from fastapi import APIRouter

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.get("")
async def list_accounts():
    return {"message": "list accounts endpoint hit ✓", "method": "GET", "path": "/accounts"}


@router.post("", status_code=201)
async def create_account():
    return {"message": "create account endpoint hit ✓", "method": "POST", "path": "/accounts"}


@router.get("/{account_id}")
async def get_account(account_id: int):
    return {"message": "get account endpoint hit ✓", "method": "GET", "path": f"/accounts/{account_id}", "account_id": account_id}


@router.patch("/{account_id}")
async def update_account(account_id: int):
    return {"message": "update account endpoint hit ✓", "method": "PATCH", "path": f"/accounts/{account_id}", "account_id": account_id}


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int):
    return None


@router.get("/{account_id}/balance")
async def get_balance(account_id: int):
    return {"message": "get balance endpoint hit ✓", "method": "GET", "path": f"/accounts/{account_id}/balance", "account_id": account_id}

