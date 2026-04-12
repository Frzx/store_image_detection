from app.core.celery_app import celery_app
from app.services.detection import detector

@celery_app.task(name='process_document')
def detect_object(document_id: str):
    results = detector.predict(document_id)
    return results