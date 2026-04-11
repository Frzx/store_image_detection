from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.document import DocumentService

db_dependency = Annotated[AsyncSession, Depends(get_db)]


def get_document_service(db: db_dependency):
    return DocumentService(db)

document_service_dep = Annotated[DocumentService,Depends(get_document_service)]