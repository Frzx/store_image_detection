from uuid import uuid4
import os
import shutil

from fastapi import APIRouter,File, UploadFile

router = APIRouter(prefix="/document",tags=['Documents'])

UPLOAD_DIR = "shared/uploads/images"


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload a file and create a DB entry"""
    document_id = uuid4()

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR,exist_ok = True)

    file_path = os.path.join(UPLOAD_DIR,f"{document_id}_{file.filename}")

    with open(file_path,'wb') as buffer:
        shutil.copyfileobj(file.file,buffer)

    return {
        "document_id": str(document_id),
        "filename": file.filename
    }