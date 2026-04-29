# OBJECT DETECTION SERVICE

Minimal layered setup:

- `app/` is the backend API and worker code
- `frontend_app/` is a separate Python/Jinja frontend
- uploaded files are stored under `shared/uploads/images`
- cropped detection artifacts are stored under `shared/artifacts`
