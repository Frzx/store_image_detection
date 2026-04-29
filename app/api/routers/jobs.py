from fastapi import APIRouter, File, HTTPException, Path, UploadFile, status

from ..dependencies import document_service_dep
from ..schemas.job import JobDetail, JobSummary, JobUploadResponse

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_image(
    document_service: document_service_dep,
    file: UploadFile = File(...),
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/jpg",
        "image/bmp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format",
        )

    document = await document_service.add(file)
    task = document_service.enqueue_detection(document)

    return {
        "document_id": str(document.id),
        "task_id": task.id,
        "status": document.status,
        "filename": document.filename,
    }


@router.get("", response_model=list[JobSummary])
async def list_jobs(document_service: document_service_dep):
    documents = await document_service.list_documents()
    return [
        {
            "document_id": str(document.id),
            "filename": document.filename,
            "status": document.status,
            "created_at": document.created_at.isoformat(),
            "detections_count": len((document.result or {}).get("detections", [])),
        }
        for document in documents
    ]


@router.get("/{document_id}", response_model=JobDetail)
async def get_job(
    document_service: document_service_dep,
    document_id: str = Path(),
):
    document = await document_service.get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found {document_id}",
        )

    return {
        "document_id": str(document.id),
        "filename": document.filename,
        "status": document.status,
        "created_at": document.created_at.isoformat(),
        "result": document.result,
    }
