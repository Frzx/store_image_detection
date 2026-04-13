from fastapi import APIRouter,File, UploadFile, Path, HTTPException,status
from celery.result import AsyncResult

from app.tasks.object_detection import detect_object
from app.core.celery_app import celery_app

from ..dependencies import document_service_dep
from ..schemas.document import DocumentUploadResponse

router = APIRouter(prefix="/document",tags=['Documents'])


@router.post("/upload",response_model=DocumentUploadResponse)
async def upload_image(
    document_service: document_service_dep,
    file: UploadFile = File(...)):
    """Upload a file and create a DB entry"""
    document = await document_service.add(file)
    image_path = f"shared/uploads/images/{document.id}_{document.filename}"
    task = detect_object.delay(str(document.id), image_path)

    return {
        "document_id": str(document.id),
        "task_id": task.id,
        "status": document.status,
        "filename": document.filename,
    }

@router.get("/tasks/{task_id}")
async def get_task_result(task_id: str):
    task = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": task.status,
    }

    if task.successful():
        response["result"] = task.result
    elif task.failed():
        response["error"] = str(task.result)

    return response


@router.get("/{document_id}")
async def get_document(
    document_service: document_service_dep,
    document_id:str = Path()
):
    document = await document_service.get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail = f"Document not found {document_id}"
        )
    
    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "status": document.status,
        "result": document.result,
    }