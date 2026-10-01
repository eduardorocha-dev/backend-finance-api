from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, computed_field


class ExportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"


class ExportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


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
    created_at: datetime

    model_config = {"from_attributes": True}

    @computed_field  # type: ignore[prop-decorator]
    @property
    def file_url(self) -> str | None:
        """Where to download the file once it's ready (None until then)."""
        if self.status != ExportStatus.DONE:
            return None
        return f"/api/v1/exports/{self.id}/download"
