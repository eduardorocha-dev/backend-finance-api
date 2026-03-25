from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Category, session)

    async def get_all_by_owner(self, owner_id: int) -> list[Category]:
        result = await self.session.execute(
            select(Category).where(Category.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self, category_id: int, owner_id: int
    ) -> Category | None:
        result = await self.session.execute(
            select(Category).where(
                Category.id == category_id,
                Category.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, category: Category, **kwargs) -> Category:
        for key, value in kwargs.items():
            setattr(category, key, value)
        await self.session.flush()
        await self.session.refresh(category)
        return category
