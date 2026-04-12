import asyncio
from uuid import UUID


from app.core.celery_app import celery_app
from app.database.models import Document
from app.database.session import AsyncSessionLocal
from app.services.detection import detector


async def update_document_status(document_id: str, status: str):
    async with AsyncSessionLocal() as session:
        document = await session.get(Document,UUID(document_id))
        if document is None:
            raise ValueError(f"Document not found : {document_id}")
        
        document.status = status
        await session.commit()

async def run_detection_task(document_id: str, image_path: str):
    try:
        await update_document_status(document_id, "PROCESSING")

        results = detector.predict(image_path)

        await update_document_status(document_id, "COMPLETED")
        return results

    except Exception:
        await update_document_status(document_id, "FAILED")
        raise


@celery_app.task(name="process_document")
def detect_object(document_id: str, image_path: str):
    return asyncio.run(run_detection_task(document_id, image_path))