# Object Detection Service

This project runs a small object-detection pipeline with:

- an ingestion/API service built with FastAPI
- an object-detection worker built with Celery
- a separate Python/Jinja frontend
- Postgres for job metadata
- Redis for the task queue

Uploaded images are stored in `shared/uploads/images`, and cropped detection artifacts are stored in `shared/artifacts`.

## Services

- `api`: receives uploads, stores jobs, exposes job APIs, and serves uploaded/artifact files
- `celery_worker`: runs object detection and saves cropped artifacts
- `frontend`: browser UI for uploading images and viewing previous jobs
- `postgres`: job metadata database
- `redis`: Celery broker/result backend

## Run With Docker Compose

From the project root:

```powershell
docker compose up --build
```

This starts:

- frontend at [http://localhost:8080](http://localhost:8080)
- API at [http://localhost:8000](http://localhost:8000)
- API health endpoint at [http://localhost:8000/health](http://localhost:8000/health)

To stop everything:

```powershell
docker compose down
```

To rebuild after code or dependency changes:

```powershell
docker compose up --build
```

To force a full clean rebuild:

```powershell
docker compose build --no-cache
docker compose up
```

## Development Compose File

There is also a development stack:

```powershell
docker compose -f docker-compose.dev.yaml up --build
```

This version:

- runs the API with `--reload`
- runs the frontend with `--reload`
- expects Postgres to be available on `host.docker.internal:5432`

Use the main `docker-compose.yaml` if you want Postgres included in the stack.

## First Run Notes

- The project runs inference on CPU using ONNX Runtime.
- If the ONNX model file is missing, the worker will try to fetch model assets from Hugging Face and create the ONNX model on first use.
- The first detection job may take longer because of model download/export and warm-up.
- You may see an ONNX Runtime GPU discovery warning in Docker logs. The app still runs on `CPUExecutionProvider`.

## Test The App

### Option 1: Use the frontend

1. Start the stack:

```powershell
docker compose up --build
```

2. Open [http://localhost:8080](http://localhost:8080)
3. Upload an image
4. Wait for the job detail page to refresh
5. Review:
   - original image
   - cropped detected objects
   - labels and confidence scores

### Option 2: Use the API directly

Upload an image:

```powershell
curl.exe -X POST -F "file=@path/to/your-image.jpg" http://localhost:8000/jobs
```

Fetch a job by id:

```powershell
curl.exe http://localhost:8000/jobs/<job-id>
```

List all jobs:

```powershell
curl.exe http://localhost:8000/jobs
```

## Useful Docker Commands

View service status:

```powershell
docker compose ps
```

Follow logs:

```powershell
docker compose logs -f
```

Follow only the worker logs:

```powershell
docker compose logs -f celery_worker
```

Follow only the API logs:

```powershell
docker compose logs -f api
```

## Project Structure

- `app/`: backend API, database, services, and Celery task code
- `frontend_app/`: separate frontend application
- `models/`: ONNX model storage
- `shared/`: uploaded images and generated artifacts
