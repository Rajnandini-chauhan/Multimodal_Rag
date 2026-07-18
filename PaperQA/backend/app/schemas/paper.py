import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ingestion_job import IngestionStatus

class IngestionJobOut(BaseModel):
    id: uuid.UUID
    status: IngestionStatus
    progress_percent: int
    error_message: str | None = None

    class Config:
        from_attributes = True


class PaperOut(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    created_at: datetime
    ingestion_job: IngestionJobOut

    class Config:
        from_attributes = True