# Smart Study Assistant

<p align="center">
  AI-powered study material analysis, collaboration, and review workflows built with FastAPI, React, PostgreSQL, Redis, Celery, DeepSeek, and GLM.
</p>

<p align="center">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white">
  <img alt="React" src="https://img.shields.io/badge/React-19-20232A?logo=react&logoColor=61DAFB">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white">
  <img alt="Redis" src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white">
  <img alt="Celery" src="https://img.shields.io/badge/Celery-5.4-37814A?logo=celery&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-black">
</p>

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Current Runtime Rules](#current-runtime-rules)
- [Architecture Snapshot](#architecture-snapshot)
- [Core Capabilities](#core-capabilities)
- [Supported File Types](#supported-file-types)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Docker](#docker)
- [Sharing and Permissions](#sharing-and-permissions)
- [Admin Access](#admin-access)
- [Testing](#testing)
- [Documentation](#documentation)
- [Operational Notes](#operational-notes)
- [License](#license)

## What This Project Does

Smart Study Assistant turns uploaded study material into reusable learning assets and collaborative workflows.

It currently supports:

- single and batch upload of documents, audio, images, and video
- AI-generated summaries, concepts, flashcards, learning paths, and knowledge graphs
- upload-grounded Q&A
- public/private visibility control
- direct sharing and study-group sharing
- comments on uploaded materials
- study-group chat and shared group files
- an admin console for users, uploads, stats, and platform settings

## Current Runtime Rules

> Runtime database is PostgreSQL only.  
> SQLAlchemy should use `postgresql+psycopg2://...`.  
> SQLite is only used by tests.

> Text tasks stay on DeepSeek.  
> Audio, OCR, and video extraction go through GLM.

> For reliable asynchronous processing, run Redis and the Celery worker.  
> If queue dispatch fails entirely, the API can fall back to in-process execution. If jobs are queued but no worker consumes them, uploads remain pending.

## Architecture Snapshot

```mermaid
flowchart LR
    U[User] --> F[React Frontend]
    F --> B[FastAPI Backend]
    B --> P[(PostgreSQL)]
    B --> R[(Redis)]
    B --> W[Celery Worker]
    W --> G[GLM]
    W --> D[DeepSeek]
    W --> P
```

Processing flow:

1. a file is uploaded through the frontend
2. FastAPI stores metadata in PostgreSQL and the file on disk
3. Celery picks up the upload job
4. GLM extracts media content when needed
5. DeepSeek generates text-first learning artifacts
6. the frontend reads the finished analysis and collaboration data

## Core Capabilities

| Area | Current behavior |
| --- | --- |
| Uploads | Single and batch upload, retry failed jobs, delete files, course assignment, status tracking |
| Analysis | Summary, concepts, flashcards, transcript, Q&A, knowledge graph, learning path |
| Collaboration | Direct share, group share, comments, shared-materials page, study-group chat |
| Visibility | `Private` and `Public` upload-level toggle |
| Admin | Users, uploads, platform stats, and configurable limits |
| Deployment | Local infra compose, production-style compose, Windows bootstrap script |

## Supported File Types

| Category | Extensions |
| --- | --- |
| Documents | `pdf`, `pptx`, `ppt`, `docx` |
| Audio | `mp3`, `wav` |
| Images | `png`, `jpg`, `jpeg` |
| Video | `mp4`, `mov` |

## AI Routing

### DeepSeek

DeepSeek is used for:

- summaries
- key concepts
- flashcards
- knowledge graph generation
- learning path generation
- upload-grounded chat responses

### GLM

GLM is used for:

- audio transcription
- image OCR
- PDF OCR
- video audio extraction and frame-level understanding

## Repository Layout

This is the source-oriented structure of the project. It intentionally omits generated local directories such as `backend/venv`, `frontend/node_modules`, `frontend/dist`, and cache folders.

```text
ai--main/
|-- backend/
|   |-- app/
|   |   |-- api/           # FastAPI route modules
|   |   |-- core/          # config, database, auth, validation
|   |   |-- models/        # SQLAlchemy models
|   |   |-- schemas/       # Pydantic schemas
|   |   |-- services/      # AI, permissions, business logic
|   |   |-- workers/       # Celery app and async tasks
|   |   |-- main.py        # FastAPI app entry
|   |   `-- __init__.py
|   |-- tests/             # backend test suite
|   |-- .env.example
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/    # reusable UI blocks
|   |   |-- contexts/      # auth and theme context
|   |   |-- pages/         # route-level pages
|   |   |-- services/      # axios client and helpers
|   |   |-- __tests__/     # frontend tests
|   |   |-- App.jsx
|   |   |-- index.css
|   |   `-- main.jsx
|   |-- public/
|   |-- Dockerfile
|   |-- package.json
|   |-- vite.config.js
|   `-- vitest.config.js
|-- docs/
|   |-- API.md
|   |-- ARCHITECTURE.md
|   `-- USER_GUIDE.md
|-- nginx/
|-- sql/
|   `-- init_postgres.sql
|-- .github/
|   `-- workflows/
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- install_windows.ps1
`-- README.md
```

## Quick Start

### Prerequisites

- Python 3.12 recommended
- Node.js 20+ recommended
- PostgreSQL 16 compatible runtime
- Redis 7 compatible runtime
- Docker Desktop if you want infra in containers

### 1. Start PostgreSQL and Redis

If you want local infra via Docker:

```powershell
docker compose up -d postgres redis
```

If PostgreSQL is already installed locally and you want the expected role/database:

```powershell
psql -U postgres -f sql/init_postgres.sql
```

### 2. Configure backend environment

Copy the backend template:

```powershell
Copy-Item backend/.env.example backend/.env
```

Minimum required values:

```env
DATABASE_URL=postgresql+psycopg2://studyapp:studyapp123@localhost:5432/smart_study
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production

AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=your-deepseek-key

ZHIPU_API_KEY=your-glm-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_ASR_MODEL=glm-asr-2512
GLM_VISION_MODEL=glm-4.6v
GLM_OCR_MODEL=glm-ocr
```

Optional values:

```env
AI_API_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
MAX_UPLOADS_PER_USER=100
MAX_UPLOAD_SIZE_MB=50
MAX_AUDIO_MINUTES=120
MAX_PDF_PAGES=500

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=465
MAIL_SERVER=smtp.qq.com
```

Notes:

- `AI_API_KEY` is only a fallback for the DeepSeek client.
- the backend loads both root `.env` and `backend/.env`
- `backend/.env` overrides root `.env`

### 3. Install and run the backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend URL:

- `http://127.0.0.1:8000`
- health check: `http://127.0.0.1:8000/api/health`

### 4. Start the worker

Windows:

```powershell
cd backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info --pool=solo
```

Linux or macOS:

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### 5. Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

- `http://127.0.0.1:5173`

## Environment Variables

There are two templates in this repository:

- root: [`.env.example`](./.env.example)
- backend-local: [`backend/.env.example`](./backend/.env.example)

Key variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis broker/result backend |
| `SECRET_KEY` | JWT and token signing secret |
| `DEEPSEEK_API_KEY` | DeepSeek text task key |
| `AI_PROVIDER` | Current text provider, expected `deepseek` |
| `AI_BASE_URL` | DeepSeek API base URL |
| `LLM_MODEL` | Text model name |
| `ZHIPU_API_KEY` | GLM key |
| `GLM_*` | Media model names and behavior tuning |
| `MAX_*` | Upload and processing limits |
| `MAIL_*` | Optional email verification / password reset config |

## Docker

### Local infra only

[`docker-compose.yml`](./docker-compose.yml) starts:

- PostgreSQL
- Redis

Use this when you want to run FastAPI, Celery, and Vite directly on your machine.

```powershell
docker compose up -d postgres redis
```

### Full production-style stack

[`docker-compose.prod.yml`](./docker-compose.prod.yml) starts:

- PostgreSQL
- Redis
- FastAPI backend
- Celery worker
- React frontend container
- Nginx reverse proxy

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

Default public entry point after boot:

- `http://127.0.0.1`

## Sharing and Permissions

Current read-access model:

- owner
- directly shared user
- member of a group the upload was shared into
- public viewer when `is_shared=true`
- admin

Practical behavior:

- `Private` means not globally public
- `Private + group share` means only that group can open it
- `Public` means the file appears in `Shared With Me`
- admins can open any upload analysis page

## Collaboration Behavior

The current product behavior is:

- shared users can open the same analysis page as the owner
- non-owners see `Read Only` where editing is owner-only
- comments are available on upload detail pages
- study-group chat supports text messages
- group file sharing uses already-uploaded completed materials, not raw file upload inside chat

## Admin Access

Admin route:

- `/admin`

Important:

- there is no automatic default admin bootstrap
- newly registered users are normal users by default
- the navbar only shows the admin entry when `is_admin=true`

Example manual promotion in PostgreSQL:

```sql
UPDATE users
SET is_admin = TRUE
WHERE username = 'your-username';
```

## Testing

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

Frontend production build:

```powershell
cd frontend
npm run build
```

## Documentation

Detailed project docs live in:

- [docs/API.md](./docs/API.md)
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/USER_GUIDE.md](./docs/USER_GUIDE.md)

## Operational Notes

### OCR path

Current OCR behavior:

- primary path: GLM `layout_parsing`
- image and PDF payloads are sent as data URLs
- fallback path: local PDF extraction or `pytesseract`

### Upload processing

The worker stores output back into the relational model:

- transcript
- summary
- concepts
- flashcards
- language metadata

### Docker upload volume

The production compose file mounts the same uploads directory into backend and worker containers:

- backend: `/app/uploads`
- worker: `/app/uploads`

That shared volume is required so asynchronous media processing can read uploaded files.

### CORS

Local frontend origins already allowed in the backend:

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## License

MIT
