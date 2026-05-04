# Video Detection Service

This repo is intentionally split into separate deployable units:

- `backend/`: API + Celery worker + ONNX inference runtime
- `frontend/`: browser UI
- `tools/model_builder/`: one-time model preparation utility
- `deploy/`: Docker Compose orchestration

Uploaded videos are processed into annotated frames stored in `shared/frames`. The worker samples frames every `0.5` seconds and keeps only `person` and `cell phone` detections from the current model.

## Quick Start

From the repo root:

```powershell
docker compose -f deploy/docker-compose.yaml --profile tools run --rm model_builder
docker compose -f deploy/docker-compose.yaml up --build
```

Then open:

- frontend at [http://localhost:8080/jobs](http://localhost:8080/jobs)
- API at [http://localhost:8000](http://localhost:8000)

## Services

- `api`: receives video uploads, stores jobs, exposes job APIs, and serves generated frame files
- `celery_worker`: extracts frames, runs object detection, and saves annotated frames
- `model_builder`: on-demand utility service that downloads or exports the ONNX model plus local config assets into the shared model volume
- `frontend`: browser UI for uploading videos and viewing previous jobs
- `postgres`: job metadata database
- `redis`: Celery broker/result backend

## Prepare The Model

Before starting the runtime stack for the first time, or whenever you want to refresh model assets:

```powershell
docker compose -f deploy/docker-compose.yaml --profile tools run --rm model_builder
```

The model builder writes the ONNX model and related local config files into the shared `model_data` Docker volume. If the files are already present, it exits quickly and skips rebuilding.

## Run With Docker Compose

From the project root:

```powershell
docker compose -f deploy/docker-compose.yaml up --build
```

This starts:

- frontend at [http://localhost:8080](http://localhost:8080)
- API at [http://localhost:8000](http://localhost:8000)
- API health endpoint at [http://localhost:8000/health](http://localhost:8000/health)

To stop everything:

```powershell
docker compose -f deploy/docker-compose.yaml down
```

To rebuild after code or dependency changes:

```powershell
docker compose -f deploy/docker-compose.yaml up --build
```

To force a full clean rebuild:

```powershell
docker compose -f deploy/docker-compose.yaml build --no-cache
docker compose -f deploy/docker-compose.yaml up
```

## Development Compose File

There is also a development stack:

```powershell
docker compose -f deploy/docker-compose.dev.yaml --profile tools run --rm model_builder
docker compose -f deploy/docker-compose.dev.yaml up --build
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
- Runtime services do not download model weights or export ONNX on startup.
- If model assets are missing, the API or worker will fail fast with a clear error telling you to run the model builder utility step.
- The first model preparation run may take longer because it may need to download or export the ONNX artifact.
- The worker uses `ffmpeg` to extract frames every `0.5` seconds before running detection.
- You may see an ONNX Runtime GPU discovery warning in Docker logs. The app still runs on `CPUExecutionProvider`.

## Container Layout

- `backend/Dockerfile`: backend runtime image for API and worker
- `frontend/Dockerfile`: lightweight frontend image with only UI dependencies
- `tools/model_builder/Dockerfile`: one-time model builder image with heavy model-prep dependencies
- `model_data` Docker volume: shared ONNX model/config artifacts consumed by runtime services

## Test The App

### Option 1: Use the frontend

1. Start the stack:

```powershell
docker compose -f deploy/docker-compose.yaml --profile tools run --rm model_builder
docker compose -f deploy/docker-compose.yaml up --build
```

2. Open [http://localhost:8080](http://localhost:8080)
3. Upload a video
4. Wait for the job detail page to refresh
5. Review:
   - annotated frames
   - frame timestamps
   - `person` and `cell phone` detections with bounding boxes
   - `0 detections` on frames without a matching object

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
docker compose -f deploy/docker-compose.yaml ps
```

Follow logs:

```powershell
docker compose -f deploy/docker-compose.yaml logs -f
```

Follow only the worker logs:

```powershell
docker compose -f deploy/docker-compose.yaml logs -f celery_worker
```

Follow only the model builder logs:

```powershell
docker compose -f deploy/docker-compose.yaml --profile tools logs -f model_builder
```

Follow only the API logs:

```powershell
docker compose -f deploy/docker-compose.yaml logs -f api
```

Follow only the frontend logs:

```powershell
docker compose -f deploy/docker-compose.yaml logs -f frontend
```

## Project Structure

- `backend/`: backend code, dependencies, and Dockerfile
- `frontend/`: frontend code, dependencies, and Dockerfile
- `deploy/`: production and development Compose files
- `tools/model_builder/prepare_model.py`: one-shot ONNX preparation entrypoint for the model-builder utility container
- `tools/model_builder/`: standalone one-time utility project with its own dependencies and Dockerfile
- `models/`: ONNX model storage inside the shared Docker volume
- `shared/`: uploaded videos during processing and generated frame artifacts
