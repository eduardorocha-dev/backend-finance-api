from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import ExportJob, ExportStatus
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[ExportJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ExportJob, session)

    async def get_all_by_owner(self, owner_id: int) -> list[ExportJob]:
        result = await self.session.execute(
            select(ExportJob)
            .where(ExportJob.owner_id == owner_id)
            .order_by(ExportJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, export_id: int, owner_id: int) -> ExportJob | None:
        result = await self.session.execute(
            select(ExportJob).where(
                ExportJob.id == export_id,
                ExportJob.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        export_job: ExportJob,
        status: ExportStatus,
        file_url: str | None = None,
    ) -> ExportJob:
        export_job.status = status
        if file_url is not None:
            export_job.file_url = file_url
        await self.session.flush()
        await self.session.refresh(export_job)
        return export_job
