from typing import Any

from pydantic import BaseModel


class JobUploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    task_id: str


class JobSummary(BaseModel):
    document_id: str
    filename: str
    status: str
    created_at: str
    detections_count: int


class JobDetail(BaseModel):
    document_id: str
    filename: str
    status: str
    created_at: str
    result: dict[str, Any] | None = None
