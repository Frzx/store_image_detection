from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import jobs
from app.database.session import create_db_tables


@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    yield


app = FastAPI(lifespan=lifespan_handler)

shared_dir = Path("shared")
shared_dir.mkdir(parents=True, exist_ok=True)

app.mount("/files", StaticFiles(directory=shared_dir), name="files")
app.include_router(jobs.router)


@app.get("/health")
def check_health():
    return {"status": "healthy"}
