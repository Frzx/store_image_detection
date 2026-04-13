from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import database_settings

engine = create_engine(url = database_settings.POSTGRES_SYNC_URL)

SyncSessionLocal = sessionmaker(bind=engine,autoflush=False)