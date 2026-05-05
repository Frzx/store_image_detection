# Video Detection Service

This repo is intentionally split into separate deployable units:

- `backend/`: API + Celery worker + ONNX inference runtime
- `frontend/`: browser UI
- `tools/model_builder/`: one-time model preparation utility
- `deploy/`: Docker Compose orchestration, including a dedicated model-builder Compose file

Uploaded videos are processed into annotated frames stored in `shared/frames`. The worker samples frames every `0.5` seconds and keeps only `person` and `cell phone` detections from the current model.

## Model Artifacts

Model artifacts live in a versioned local artifact store. The intended layout is:

```text
models/
  object-detector/
    v1/
      model.onnx
      config.json
      preprocessor_config.json
      metadata.json
  object-detector-phone-tuned/
    v1/
      ...
```

The backend loads one configured model artifact directory at a time using:

- `MODEL_ARTIFACT_ROOT`
- `MODEL_NAME`
- `MODEL_VERSION`

## Quick Start

From the repo root:

```powershell
# 1. Create the model artifact bundle in the artifact store
docker compose -f deploy/docker-compose.model-builder.yaml run --rm model_builder

# 2. Start the runtime stack
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

Before starting the runtime stack for the first time on a new machine, you must create the model artifact bundle. Run:

```powershell
docker compose -f deploy/docker-compose.model-builder.yaml build --no-cache
docker compose -f deploy/docker-compose.model-builder.yaml run --rm model_builder
```

The model builder writes the ONNX model and related local config files into the local [models](C:/Users/91963/projects/object_detection_tesco/models) directory on your machine. With the current configuration, it creates:

```text
models/
  object-detector/
    v1/
      model.onnx
      config.json
      preprocessor_config.json
      metadata.json
```

After that, start the runtime stack with:

```powershell
docker compose -f deploy/docker-compose.yaml up --build
```

If you run the model builder again later, it checks whether the artifact bundle already exists and skips rebuilding when the files are already present.

If you change code under [tools/model_builder](C:/Users/91963/projects/object_detection_tesco/tools/model_builder) or its Dockerfile, rebuild the model-builder image before running it again:

```powershell
docker compose -f deploy/docker-compose.model-builder.yaml build --no-cache
docker compose -f deploy/docker-compose.model-builder.yaml run --rm model_builder
```

After a successful run, you should be able to open [models](C:/Users/91963/projects/object_detection_tesco/models) on the host machine and see:

```text
models/
  object-detector/
    v1/
      model.onnx
      config.json
      preprocessor_config.json
      metadata.json
```

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
docker compose -f deploy/docker-compose.model-builder.yaml run --rm model_builder
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
- First-time setup is a 2-step process: create model artifacts first, then start the runtime stack.
- Runtime services do not download model weights or export ONNX on startup.
- If model assets are missing, the API or worker will fail fast with a clear error telling you to run the model builder utility step.
- The first model preparation run may take longer because it may need to download or export the ONNX artifact.
- Model artifacts are stored directly in the host `models/` directory and are shared with the runtime containers through bind mounts.
- The worker uses `ffmpeg` to extract frames every `0.5` seconds before running detection.
- You may see an ONNX Runtime GPU discovery warning in Docker logs. The app still runs on `CPUExecutionProvider`.

## Container Layout

- `backend/Dockerfile`: backend runtime image for API and worker
- `frontend/Dockerfile`: lightweight frontend image with only UI dependencies
- `tools/model_builder/Dockerfile`: one-time model builder image with heavy model-prep dependencies
- host `models/` directory: shared local artifact store mounted into the model builder, API, and worker containers

## Test The App

### Option 1: Use the frontend

1. Start the stack:

```powershell
docker compose -f deploy/docker-compose.model-builder.yaml run --rm model_builder
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
docker compose -f deploy/docker-compose.model-builder.yaml logs -f model_builder
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
- `deploy/`: production, development, and model-builder Compose files
- `deploy/docker-compose.model-builder.yaml`: standalone Compose file for one-time model preparation
- `tools/model_builder/prepare_model.py`: one-shot ONNX preparation entrypoint for the model-builder utility container
- `tools/model_builder/`: standalone one-time utility project with its own dependencies and Dockerfile
- `models/`: local host-side model artifact store shared across containers
- `shared/`: uploaded videos during processing and generated frame artifacts
