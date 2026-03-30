from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.export import ExportCreate, ExportRead
from app.services.export import ExportService

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportRead, status_code=status.HTTP_202_ACCEPTED)
async def request_export(
    data: ExportCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    export_job = await ExportService(session).create(current_user.id, data)
    await session.commit()
    return export_job


@router.get("/{export_id}", response_model=ExportRead)
async def get_export_status(
    export_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    return await ExportService(session).get(current_user.id, export_id)
