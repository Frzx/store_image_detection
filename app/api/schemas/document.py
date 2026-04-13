from typing import Any

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    task_id: str


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    result: dict[str, Any] | None = None