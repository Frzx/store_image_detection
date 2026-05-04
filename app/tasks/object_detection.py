from datetime import datetime
from pathlib import Path
import shutil
from uuid import UUID

from app.core.celery_app import celery_app
from app.config import model_settings
from app.database.models import Document
from app.database.sync_session import SyncSessionLocal
from app.services.detection import get_detector
from app.services.video import extract_frames


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
def detect_object(document_id: str, video_path: str):
    uploaded_video_path = Path(video_path)
    frame_output_dir = Path("shared") / "frames" / document_id / "source"
    try:
        update_document_result(document_id, "PROCESSING")

        frame_paths = extract_frames(
            uploaded_video_path,
            frame_output_dir,
            model_settings.FRAME_EXTRACTION_INTERVAL_SECONDS,
        )
        detector = get_detector()
        frames = [
            detector.detect_frame(
                frame_path=frame_path,
                document_id=document_id,
                frame_index=index,
                timestamp_seconds=(index - 1) * model_settings.FRAME_EXTRACTION_INTERVAL_SECONDS,
            )
            for index, frame_path in enumerate(frame_paths, start=1)
        ]
        if frame_output_dir.exists():
            shutil.rmtree(frame_output_dir)

        results = {
            "filename": uploaded_video_path.name,
            "status": "success",
            "frame_interval_seconds": model_settings.FRAME_EXTRACTION_INTERVAL_SECONDS,
            "frames_count": len(frames),
            "detections_count": sum(frame["detections_count"] for frame in frames),
            "frames": frames,
            "metadata": {
                "model": str(detector.model_path),
                "runtime": "onnxruntime",
                "provider": "CPUExecutionProvider",
                "filtered_labels": ["person", "cell phone"],
            },
        }

        update_document_result(document_id, "COMPLETED", results)
        return results

    except Exception:
        annotated_dir = Path("shared") / "frames" / document_id
        if annotated_dir.exists():
            shutil.rmtree(annotated_dir)
        update_document_result(document_id, "FAILED")
        raise
    finally:
        if uploaded_video_path.exists():
            uploaded_video_path.unlink()
        if frame_output_dir.exists():
            shutil.rmtree(frame_output_dir)
