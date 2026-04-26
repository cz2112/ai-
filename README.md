# Smart Study Assistant

Smart Study Assistant is a full-stack study platform built with FastAPI, React, PostgreSQL, Redis, Celery, DeepSeek, and GLM.

It accepts study materials, extracts content, generates summaries / key concepts / flashcards, supports multi-turn Q&A, knowledge graphs, comments, sharing, study groups, and an admin console.

## Current runtime model routing

- Text generation: DeepSeek
  - summaries
  - key concepts
  - flashcards
  - knowledge graph
  - learning path
  - contextual Q&A
- Media and OCR: GLM
  - audio transcription
  - image OCR
  - PDF OCR
  - video audio + frame analysis

## Supported file types

- Documents: `pdf`, `pptx`, `ppt`, `docx`
- Audio: `mp3`, `wav`
- Images: `png`, `jpg`, `jpeg`
- Video: `mp4`, `mov`

## Runtime stack

- Backend: FastAPI + SQLAlchemy + Pydantic
- Frontend: React + Vite + Tailwind
- Database: PostgreSQL
- Queue / broker: Redis + Celery
- Text AI: DeepSeek
- Media AI: GLM

## Important runtime notes

- Runtime database is PostgreSQL only.
- The configured SQLAlchemy URL should use `postgresql+psycopg2://...`.
- SQLite is used only in automated tests.
- Upload analysis depends on a running Celery worker. If the worker is down, uploads will stay pending or fail.
- In Docker, the backend container and Celery worker must share the same uploads volume. This repository is configured that way.

## Repository layout

```text
.
  backend/
    app/
      api/
      core/
      models/
      schemas/
      services/
      workers/
    tests/
    Dockerfile
    requirements.txt
  frontend/
    src/
    Dockerfile
    package.json
  nginx/
  sql/
  docker-compose.yml
  docker-compose.prod.yml
  README.md
```

## Environment files

There are two templates:

- Root: `.env.example`
  - mainly for Docker Compose and shared defaults
- Backend: `backend/.env.example`
  - mainly for local backend development

The backend loads both root `.env` and `backend/.env`, with `backend/.env` taking precedence.

## Local development

### 1. Start PostgreSQL and Redis

If you want local infra through Docker:

```powershell
docker compose up -d postgres redis
```

If you already have PostgreSQL installed locally, you can bootstrap the expected database and role with:

```powershell
psql -U postgres -f sql/init_postgres.sql
```

### 2. Configure backend environment

```powershell
Copy-Item backend/.env.example backend/.env
```

Set the required values below, and add the optional ones if you use those features:

```env
DATABASE_URL=postgresql+psycopg2://studyapp:studyapp123@localhost:5432/smart_study
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production

DEEPSEEK_API_KEY=your-deepseek-key
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
AI_API_KEY=

ZHIPU_API_KEY=your-glm-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_ASR_MODEL=glm-asr-2512
GLM_VISION_MODEL=glm-4.6v
GLM_OCR_MODEL=glm-ocr

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=465
MAIL_SERVER=smtp.qq.com
```

`AI_API_KEY` is only a fallback for the DeepSeek text client. The preferred runtime key is `DEEPSEEK_API_KEY`.

`MAIL_*` values are optional and are only needed if you want the email verification or password reset flows to send mail successfully.

### 3. Install and run the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend health check:

```text
http://127.0.0.1:8000/api/health
```

### 4. Start the Celery worker

Windows local run:

```powershell
cd backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### 5. Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://127.0.0.1:5173
```

## Docker

### Local infra only

`docker-compose.yml` starts:

- PostgreSQL
- Redis

Use it when you want to run FastAPI / Celery / Vite directly on your machine, but keep DB and Redis in containers.

### Production-style stack

`docker-compose.prod.yml` starts:

- PostgreSQL
- Redis
- FastAPI backend
- Celery worker
- React frontend
- Nginx reverse proxy

Run:

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

## Admin

- Admin UI route: `/admin`
- Navbar link is shown only when the authenticated user has `is_admin=true`
- No default admin user is created by the application at startup

## File visibility model

- `Private`
  - visible to the owner
  - visible to explicitly shared users
  - visible to members of groups the file is shared into
- `Public`
  - visible in the shared materials list to other users

`Private + shared to group` means only that group can access it. It does not become globally public.

## Tests

Backend:

```powershell
cd backend
pytest tests -v
```

Frontend:

```powershell
cd frontend
npm test
```

## Operational notes

- OCR now uses GLM `layout_parsing` with data URL payloads for image and PDF inputs.
- The backend falls back to local PDF extraction or `pytesseract` only when the GLM path is unavailable or fails.
- The production compose file shares `/app/uploads` between backend and worker so media processing can read uploaded files correctly.

## License

MIT
