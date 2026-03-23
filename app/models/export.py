from __future__ import annotations

from datetime import date
from enum import Enum

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ExportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"


class ExportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ExportJob(Base, TimestampMixin):
    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    format: Mapped[ExportFormat] = mapped_column(SAEnum(ExportFormat), nullable=False)
    status: Mapped[ExportStatus] = mapped_column(
        SAEnum(ExportStatus), nullable=False, default=ExportStatus.PENDING
    )
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    # Populated by the Celery task once the file is generated
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="exports")
