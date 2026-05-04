# Video Detection Service

This project runs a small object-detection pipeline with:

- an ingestion/API service built with FastAPI
- an object-detection worker built with Celery
- a separate Python/Jinja frontend
- Postgres for job metadata
- Redis for the task queue

Uploaded videos are processed into annotated frames stored in `shared/frames`. The worker samples frames every `0.5` seconds and keeps only `person` and `cell phone` detections from the current model.

## Services

- `api`: receives video uploads, stores jobs, exposes job APIs, and serves generated frame files
- `celery_worker`: extracts frames, runs object detection, and saves annotated frames
- `frontend`: browser UI for uploading videos and viewing previous jobs
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

## Local Development Requirements

- Python `3.11+`
- `ffmpeg` available on your `PATH`
- Postgres
- Redis

To verify `ffmpeg` is available locally:

```powershell
ffmpeg -version
```

## First Run Notes

- The project runs inference on CPU using ONNX Runtime.
- If the ONNX model file is missing, the worker will try to fetch model assets from Hugging Face and create the ONNX model on first use.
- The first detection job may take longer because of model download/export and warm-up.
- The worker uses `ffmpeg` to extract frames every `0.5` seconds before running detection.
- You may see an ONNX Runtime GPU discovery warning in Docker logs. The app still runs on `CPUExecutionProvider`.

## Test The App

### Option 1: Use the frontend

1. Start the stack:

```powershell
docker compose up --build
```

2. Open [http://localhost:8080](http://localhost:8080)
3. Upload a video
4. Wait for the job detail page to refresh
5. Review:
   - annotated frames
   - frame timestamps
   - `person` and `cell phone` detections with bounding boxes

### Option 2: Use the API directly

Upload a video:

```powershell
curl.exe -X POST -F "file=@path/to/your-video.mp4" http://localhost:8000/jobs
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
- `shared/`: uploaded videos during processing and generated frame artifacts
