from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    filename: str
    task_id: str