from fastapi import APIRouter
from app.schemas.export import ExportCreate, ExportRead

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", response_model=ExportRead, status_code=202)
async def request_export(data: ExportCreate):
    return {
        "id": 1,
        "format": data.format,
        "status": "pending",
        "date_from": data.date_from,
        "date_to": data.date_to,
        "file_url": None,
        "created_at": "2024-03-01T00:00:00",
    }


@router.get("/{export_id}", response_model=ExportRead)
async def get_export_status(export_id: int):
    return {
        "id": export_id,
        "format": "csv",
        "status": "done",
        "date_from": "2024-03-01",
        "date_to": "2024-03-31",
        "file_url": "https://fake-url.com/export.csv",
        "created_at": "2024-03-01T00:00:00",
    }
