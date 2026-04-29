from datetime import datetime
from uuid import UUID

from app.core.celery_app import celery_app
from app.database.models import Document
from app.database.sync_session import SyncSessionLocal
from app.services.detection import get_detector


def update_document_result(document_id: str, status: str, result: dict | None = None):
    with SyncSessionLocal() as session:
        document = session.get(Document, UUID(document_id))
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        document.status = status
        if result is not None:
            document.result = result
        document.updated_at = datetime.now()

        session.commit()


@celery_app.task(name="process_document")
def detect_object(document_id: str, image_path: str):
    try:
        update_document_result(document_id, "PROCESSING")

        results = get_detector().predict(document_id, image_path)

        update_document_result(document_id, "COMPLETED", results)
        return results

    except Exception:
        update_document_result(document_id, "FAILED")
        raise
