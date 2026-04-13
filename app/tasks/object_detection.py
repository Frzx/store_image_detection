from uuid import UUID

from app.core.celery_app import celery_app
from app.database.models import Document
from app.database.sync_session import SyncSessionLocal
from app.services.detection import detector


def update_document_status(document_id: str, status: str):
    with SyncSessionLocal() as session:
        document = session.get(Document,UUID(document_id))
        if document is None:
            raise ValueError(f"Document not found : {document_id}")
        
        document.status = status
        session.commit()

def run_detection_task(document_id: str, image_path: str):
    try:
        update_document_status(document_id, "PROCESSING")

        results = detector.predict(image_path)

        update_document_status(document_id, "COMPLETED")
        return results

    except Exception:
        update_document_status(document_id, "FAILED")
        raise


@celery_app.task(name="process_document")
def detect_object(document_id: str, image_path: str):
    return run_detection_task(document_id, image_path)