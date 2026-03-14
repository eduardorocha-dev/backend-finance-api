from fastapi import APIRouter

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("")
async def list_budgets():
    return {"message": "list budgets endpoint hit ✓", "method": "GET", "path": "/budgets"}


@router.post("", status_code=201)
async def create_budget():
    return {"message": "create budget endpoint hit ✓", "method": "POST", "path": "/budgets"}


@router.get("/usage")
async def get_usage():
    return {"message": "get budget usage endpoint hit ✓", "method": "GET", "path": "/budgets/usage"}


@router.get("/{budget_id}")
async def get_budget(budget_id: int):
    return {"message": "get budget endpoint hit ✓", "method": "GET", "path": f"/budgets/{budget_id}", "budget_id": budget_id}


@router.patch("/{budget_id}")
async def update_budget(budget_id: int):
    return {"message": "update budget endpoint hit ✓", "method": "PATCH", "path": f"/budgets/{budget_id}", "budget_id": budget_id}


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(budget_id: int):
    return None

