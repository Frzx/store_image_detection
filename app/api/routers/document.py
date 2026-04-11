from fastapi import APIRouter,File, UploadFile

from ..dependencies import document_service_dep
from ..schemas.document import DocumentUploadResponse

router = APIRouter(prefix="/document",tags=['Documents'])


@router.post("/upload",response_model=DocumentUploadResponse)
async def upload_image(
    document_service: document_service_dep,
    file: UploadFile = File(...)):
    """Upload a file and create a DB entry"""
    document = await document_service.add(file)
    return {"document_id": str(document.id), "status": document.status, "filename": document.filename}