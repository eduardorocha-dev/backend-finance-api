from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import ExportJob
from app.repositories.export import ExportRepository
from app.schemas.export import ExportCreate


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ExportRepository(session)

    async def create(self, user_id: int, data: ExportCreate) -> ExportJob:
        if data.date_from > data.date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_from must be before date_to",
            )

        export_job = await self.repo.create(
            owner_id=user_id,
            format=data.format,
            date_from=data.date_from,
            date_to=data.date_to,
        )

        # Dispatch background task — import here to avoid circular imports at module load
        from app.workers.tasks import generate_export

        generate_export.delay(export_job.id)

        return export_job

    async def get(self, user_id: int, export_id: int) -> ExportJob:
        export_job = await self.repo.get_by_id_and_owner(export_id, user_id)
        if export_job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Export job not found"
            )
        return export_job
