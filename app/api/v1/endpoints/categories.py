from fastapi import APIRouter

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
async def list_categories():
    return {"message": "list categories endpoint hit ✓", "method": "GET", "path": "/categories"}


@router.post("", status_code=201)
async def create_category():
    return {"message": "create category endpoint hit ✓", "method": "POST", "path": "/categories"}


@router.get("/{category_id}")
async def get_category(category_id: int):
    return {"message": "get category endpoint hit ✓", "method": "GET", "path": f"/categories/{category_id}", "category_id": category_id}


@router.patch("/{category_id}")
async def update_category(category_id: int):
    return {"message": "update category endpoint hit ✓", "method": "PATCH", "path": f"/categories/{category_id}", "category_id": category_id}


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int):
    return None

