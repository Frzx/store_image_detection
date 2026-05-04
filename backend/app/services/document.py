import shutil
from pathlib import Path
from uuid import UUID, uuid4

from celery.result import AsyncResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document

from .base import BaseService

SHARED_DIR = Path("shared")
UPLOAD_DIR = SHARED_DIR / "uploads" / "videos"


class DocumentService(BaseService[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


    async def add(self, file):
        document_id = uuid4()
        original_name = Path(file.filename or "upload").name
        file_path = self.get_upload_path(document_id, original_name)

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        doc = Document(
            id=document_id,
            filename=original_name,
            content_type=file.content_type,
            status="UPLOADED",
        )

        return await self._add(doc)

    async def get_document(self, document_id: str):
        return await self._get(UUID(document_id))

    async def list_documents(self) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def enqueue_detection(self, document: Document) -> AsyncResult:
        from app.tasks.object_detection import detect_object

        video_path = self.get_upload_path(document.id, document.filename)
        return detect_object.delay(str(document.id), str(video_path))

    @staticmethod
    def get_upload_path(document_id: UUID | str, filename: str) -> Path:
        return UPLOAD_DIR / f"{document_id}_{filename}"
