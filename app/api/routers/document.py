from uuid import uuid4
import os
import shutil

from fastapi import APIRouter,File, UploadFile

from app.database.models import Document

from ..dependencies import db_dependency
from ..schemas.document import DocumentUploadResponse

router = APIRouter(prefix="/document",tags=['Documents'])

UPLOAD_DIR = "shared/uploads/images"


@router.post("/upload",response_model=DocumentUploadResponse)
async def upload_image(
    db: db_dependency,
    file: UploadFile = File(...)):
    """Upload a file and create a DB entry"""
    document_id = uuid4()

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR,exist_ok = True)

    file_path = os.path.join(UPLOAD_DIR,f"{document_id}_{file.filename}")

    with open(file_path,'wb') as buffer:
        shutil.copyfileobj(file.file,buffer)

    doc = Document(
        id = document_id,
        filename = file.filename,
        content_type = file.content_type,
        status = "UPLOADED"
    )

    db.add(doc)
    await db.commit()

    return {
        "document_id": str(document_id),
        "status": "UPLOADED",
        "filename": file.filename
    }