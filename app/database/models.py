from datetime import datetime

from sqlalchemy import Column,String,Enum, DateTime
from sqlalchemy.dialects import postgresql

from .base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(postgresql.UUID(as_uuid=True),primary_key=True)
    filename = Column(String,nullable=False)
    content_type = Column(String)
    status = Column(
        Enum("UPLOADED","PROCESSING","COMPLETED","FAILED",name="document_status"),
        default = "UPLOADED"
    )
    
    created_at = Column(
        DateTime,
        default = datetime.now

    )

    updated_at = Column(
        DateTime,
        default = datetime.now
    )