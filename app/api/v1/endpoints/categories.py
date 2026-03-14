from fastapi import APIRouter
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories():
    return []


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(data: CategoryCreate):
    return {
        "id": 1,
        "name": data.name,
        "owner_id": 1,
        "parent_id": data.parent_id,
    }


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int):
    return {
        "id": category_id,
        "name": "Food",
        "owner_id": 1,
        "parent_id": None,
    }


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, data: CategoryUpdate):
    return {
        "id": category_id,
        "name": data.name or "Food",
        "owner_id": 1,
        "parent_id": data.parent_id,
    }


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: int):
    return None
