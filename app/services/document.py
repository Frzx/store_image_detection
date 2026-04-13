import os
import shutil
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document

from .base import BaseService

UPLOAD_DIR = "shared/uploads/images"

class DocumentService(BaseService[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(Document,session)
        os.makedirs(UPLOAD_DIR,exist_ok = True)


    # Add a new document
    async def add(self,file):
        document_id = uuid4()
        file_path = os.path.join(UPLOAD_DIR,f"{document_id}_{file.filename}")

        with open(file_path,'wb') as buffer:
            shutil.copyfileobj(file.file,buffer)

        doc = Document(
            id = document_id,
            filename = file.filename,
            content_type = file.content_type,
            status = "UPLOADED"
        )

        return await self._add(doc)
    

    async def get_document(self,document_id: str):
        return await self._get(UUID(document_id))