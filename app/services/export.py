from __future__ import annotations

import os

from fastapi import HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import ExportFormat, ExportJob, ExportStatus
from app.repositories.export import ExportRepository
from app.schemas.export import ExportCreate


class ExportService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ExportRepository(session)

    async def create(self, user_id: int, data: ExportCreate) -> ExportJob:
        if data.date_from > data.date_to:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

    async def download(self, user_id: int, export_id: int) -> Response:
        """The finished file: streamed from local disk, or a redirect to a short-lived S3 link."""
        from app.utils.export import S3_PREFIX, presigned_download_url

        export_job = await self.get(user_id, export_id)  # 404 if it isn't the user's
        if export_job.status != ExportStatus.DONE or not export_job.file_location:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Export is not ready yet (status: {export_job.status.value})",
            )

        location = export_job.file_location
        if location.startswith(S3_PREFIX):
            return RedirectResponse(presigned_download_url(location))
        if location.startswith("https://"):
            # exports stored before downloads went through this endpoint kept a public URL
            return RedirectResponse(location)
        if not os.path.isfile(location):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="The export file is no longer available"
            )

        extension = "csv" if export_job.format == ExportFormat.CSV else "pdf"
        return FileResponse(
            location,
            media_type="text/csv" if extension == "csv" else "application/pdf",
            filename=f"fintrack-export-{export_job.id}.{extension}",
        )
