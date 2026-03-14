from fastapi import APIRouter

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("", status_code=202)
async def request_export():
    return {"message": "request export endpoint hit ✓", "method": "POST", "path": "/exports"}


@router.get("/{export_id}")
async def get_export_status(export_id: int):
    return {"message": "get export status endpoint hit ✓", "method": "GET", "path": f"/exports/{export_id}", "export_id": export_id}

