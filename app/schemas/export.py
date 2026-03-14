from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel


class ExportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"


class ExportStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"


# ── Incoming ──────────────────────────────────────────────────────────────────

class ExportCreate(BaseModel):
    format: ExportFormat
    date_from: date
    date_to: date


# ── Outgoing ──────────────────────────────────────────────────────────────────

class ExportRead(BaseModel):
    id: int
    format: ExportFormat
    status: ExportStatus
    date_from: date
    date_to: date
    # file_url is None while the export is still being generated,
    # and populated once the Celery task finishes
    file_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
