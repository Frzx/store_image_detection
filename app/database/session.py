from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import database_settings

from . import models

engine = create_async_engine(
    url= database_settings.POSTGRES_URL
)

AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_ = AsyncSession,
        expire_on_commit = False,
    )

async def create_db_tables():
    async with engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session