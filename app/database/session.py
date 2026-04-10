from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from . import models

SQLALCHEMY_DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/object_detection"

engine = create_async_engine(
    url= SQLALCHEMY_DB_URL
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