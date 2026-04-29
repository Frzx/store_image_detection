from pathlib import Path
from urllib.parse import quote_plus

import httpx
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from frontend_app.config import frontend_settings

app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


async def fetch_jobs():
    async with httpx.AsyncClient(base_url=frontend_settings.BACKEND_API_URL, timeout=30.0) as client:
        jobs_response = await client.get("/jobs")
        jobs_response.raise_for_status()
        return jobs_response.json()


async def fetch_job(job_id: str):
    async with httpx.AsyncClient(base_url=frontend_settings.BACKEND_API_URL, timeout=30.0) as client:
        job_response = await client.get(f"/jobs/{job_id}")
        job_response.raise_for_status()
        return job_response.json()


def render_error_response(request: Request, message: str, status_code: int = 502):
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "message": message,
            "status_code": status_code,
        },
        status_code=status_code,
    )


@app.get("/")
async def home():
    return RedirectResponse(url="/jobs", status_code=302)


@app.get("/jobs")
async def list_jobs(request: Request, uploaded: str | None = None, error: str | None = None):
    try:
        jobs = await fetch_jobs()
    except httpx.HTTPStatusError as exc:
        return render_error_response(
            request,
            f"Backend returned {exc.response.status_code} while loading jobs.",
            status_code=exc.response.status_code,
        )
    except httpx.HTTPError:
        return render_error_response(
            request,
            "Could not reach the backend while loading jobs.",
        )

    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "jobs": jobs,
            "uploaded": uploaded,
            "error": error,
        },
    )


@app.post("/upload")
async def upload_job(file: UploadFile = File(...)):
    async with httpx.AsyncClient(base_url=frontend_settings.BACKEND_API_URL, timeout=120.0) as client:
        response = await client.post(
            "/jobs",
            files={"file": (file.filename, await file.read(), file.content_type or "application/octet-stream")},
        )

    if response.is_success:
        payload = response.json()
        return RedirectResponse(url=f"/jobs/{payload['document_id']}?uploaded=1", status_code=303)

    error_detail = "Upload failed"
    try:
        error_detail = response.json().get("detail", error_detail)
    except Exception:
        pass

    return RedirectResponse(url=f"/jobs?error={quote_plus(error_detail)}", status_code=303)


@app.get("/jobs/{job_id}")
async def job_detail(request: Request, job_id: str, uploaded: str | None = None):
    try:
        job = await fetch_job(job_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return render_error_response(
                request,
                "That job does not exist anymore.",
                status_code=404,
            )
        return render_error_response(
            request,
            f"Backend returned {exc.response.status_code} while loading the job.",
            status_code=exc.response.status_code,
        )
    except httpx.HTTPError:
        return render_error_response(
            request,
            "Could not reach the backend while loading the job.",
        )

    result = job.get("result") or {}
    detections = result.get("detections", [])
    rendered_detections = [
        {
            **detection,
            "image_url": (
                f"{frontend_settings.BACKEND_PUBLIC_URL.rstrip('/')}{detection['artifact_url']}"
                if detection.get("artifact_url")
                else None
            ),
            "label_display": str(detection.get("label", "unknown")).replace("_", " ").title(),
        }
        for detection in detections
    ]

    return templates.TemplateResponse(
        request,
        "job_detail.html",
        {
            "job": job,
            "uploaded": uploaded,
            "backend_public_url": frontend_settings.BACKEND_PUBLIC_URL.rstrip("/"),
            "original_image_url": result.get("original_image_url"),
            "detections": rendered_detections,
        },
    )
