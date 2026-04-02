from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CategoryRepository(session)

    async def list(self, user_id: int) -> list[Category]:
        return await self.repo.get_all_by_owner(user_id)

    async def create(self, user_id: int, data: CategoryCreate) -> Category:
        if data.parent_id is not None:
            parent = await self.repo.get_by_id_and_owner(data.parent_id, user_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found",
                )
        return await self.repo.create(
            owner_id=user_id,
            name=data.name,
            parent_id=data.parent_id,
        )

    async def get(self, user_id: int, category_id: int) -> Category:
        category = await self.repo.get_by_id_and_owner(category_id, user_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    async def update(self, user_id: int, category_id: int, data: CategoryUpdate) -> Category:
        category = await self.get(user_id, category_id)
        if data.parent_id is not None:
            if data.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="A category cannot be its own parent",
                )
            parent = await self.repo.get_by_id_and_owner(data.parent_id, user_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found",
                )
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return category
        return await self.repo.update(category, **updates)

    async def delete(self, user_id: int, category_id: int) -> None:
        category = await self.get(user_id, category_id)
        await self.repo.delete(category)
