from fastapi import FastAPI

from app.routers import document

app = FastAPI()

app.include_router(document.router)

@app.get("/health")
def check_health():
    return {'status': 'healthy'}