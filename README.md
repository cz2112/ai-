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

<p align="center">
  <a href="#quick-start"><strong>Quick Start</strong></a>
  |
  <a href="#current-ui-pages"><strong>Current UI Pages</strong></a>
  |
  <a href="#docker"><strong>Docker</strong></a>
  |
  <a href="./docs/API.md"><strong>API Docs</strong></a>
  |
  <a href="./docs/ARCHITECTURE.md"><strong>Architecture</strong></a>
</p>

> This README describes the project as it is implemented in the current repository, including the active UI routes, permission model, and runtime constraints.
>
> The structure and wording of the architecture section below are inspired by the project proposal PDF, but the technical facts are written against the current codebase and runtime configuration.

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Current Runtime Rules](#current-runtime-rules)
- [System Structure](#system-structure)
- [Core Capabilities](#core-capabilities)
- [Scenario / Workflow](#scenario--workflow)
- [Current UI Pages](#current-ui-pages)
- [Supported File Types](#supported-file-types)
- [AI Routing](#ai-routing)
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

## System Structure

### Architecture Overview

The system uses a decoupled web-and-worker architecture so the UI stays responsive while larger files are processed asynchronously.

Major runtime components in the current codebase are:

- **Frontend**: React + Vite + Tailwind for the browser UI
- **Backend**: FastAPI for REST APIs, authentication, validation, and orchestration
- **Broker**: Redis for Celery queue transport
- **Worker**: Celery for background extraction, OCR, transcription, and study-asset generation
- **Database**: PostgreSQL for persistent storage
- **Text AI**: DeepSeek for summaries, concepts, flashcards, learning path, knowledge graph, and upload-grounded Q&A
- **Media AI**: GLM for audio transcription, image OCR, PDF OCR, and video extraction
- **Reverse Proxy**: Nginx in the production-style Docker stack

### Architecture Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'fontSize': '24px',
  'fontFamily': 'Segoe UI, Arial, sans-serif',
  'textColor': '#111827',
  'primaryTextColor': '#111827',
  'secondaryTextColor': '#111827',
  'tertiaryTextColor': '#111827',
  'lineColor': '#475569',
  'edgeLabelBackground': '#ffffff'
}}}%%
flowchart TB
    User["User / 用户"]
    Frontend["Frontend<br/>React + Vite + Tailwind"]
    Nginx["Nginx<br/>static frontend + API proxy"]
    Backend["Backend<br/>FastAPI"]

    User --> Frontend --> Nginx --> Backend

    subgraph BackendModules["Backend modules / 后端模块"]
        direction LR
        Routes["Routes<br/>auth | uploads | share | chat | admin"]
        Security["Security<br/>JWT | rate limit | validation | sanitize"]
        Services["Services<br/>upload access | AI routing | email"]
    end

    subgraph Async["Async processing / 异步处理"]
        direction LR
        Redis["Redis"]
        Worker["Celery worker"]
        Extract["Extract / OCR / ASR / video"]
        Generate["Summary / concepts / flashcards"]
    end

    subgraph Data["Persistence / 数据层"]
        direction LR
        DB[("PostgreSQL<br/>users | uploads | courses | sharing | study assets")]
        Storage["Upload storage<br/>backend/uploads"]
    end

    subgraph AI["AI providers / 模型服务"]
        direction LR
        DeepSeek["DeepSeek<br/>chat | summary | concepts | flashcards<br/>graph | learning path"]
        GLM["GLM<br/>audio ASR | image OCR | PDF OCR | video"]
    end

    Backend --> Routes
    Backend --> Security
    Backend --> Services

    Backend --> DB
    Backend --> Storage
    Backend --> Redis
    Redis --> Worker --> Extract --> Generate
    Worker --> Storage
    Worker --> DB
    Extract --> GLM
    Generate --> DeepSeek
    Services --> DeepSeek

    classDef client fill:#e0f2fe,stroke:#0369a1,stroke-width:1.5px,color:#111827,font-size:22px;
    classDef edge fill:#f3f4f6,stroke:#4b5563,stroke-width:1.5px,color:#111827,font-size:22px;
    classDef backend fill:#dcfce7,stroke:#15803d,stroke-width:1.5px,color:#111827,font-size:22px;
    classDef async fill:#f3e8ff,stroke:#7e22ce,stroke-width:1.5px,color:#111827,font-size:22px;
    classDef data fill:#dbeafe,stroke:#1d4ed8,stroke-width:1.5px,color:#111827,font-size:22px;
    classDef ai fill:#fef3c7,stroke:#b45309,stroke-width:1.5px,color:#111827,font-size:22px;

    class User,Frontend client;
    class Nginx edge;
    class Backend,Routes,Security,Services backend;
    class Redis,Worker,Extract,Generate async;
    class DB,Storage data;
    class DeepSeek,GLM ai;

    style BackendModules fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#111827;
    style Async fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#111827;
    style Data fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#111827;
    style AI fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#111827;
```

**Architecture Layers:**

| Layer | Components | Description |
|-------|-----------|-------------|
| **Client** | User + Browser | Web browser interface |
| **Frontend** | React 18 + Vite + Tailwind + Router + Contexts | Single-page application with authentication and theming |
| **Gateway** | Nginx | Reverse proxy for production deployment |
| **Backend** | FastAPI 0.115 | REST API server with 5 route modules, 4 security components, 3 business services |
| **Async Processing** | Redis + Celery Worker | Message queue and background task processing (4 task types) |
| **Data** | PostgreSQL 16 + File Storage | Relational database and file system storage |
| **AI Services** | DeepSeek + GLM | Text generation (6 capabilities) and multimodal processing (4 capabilities) |

### Processing Flow

1. the user uploads a file from the frontend
2. FastAPI validates the file, stores metadata in PostgreSQL, and writes the uploaded file to disk
3. the backend enqueues a background job through Celery and Redis
4. the Celery worker extracts text, OCR output, audio transcription, or video-derived content depending on file type
5. DeepSeek generates the study assets from the extracted content
6. the worker stores transcript, summary, concepts, flashcards, and language metadata back into PostgreSQL
7. the frontend reads the finished outputs through the normal API routes

### Major Components and Responsibilities

| Component | Responsibility in the current codebase |
| --- | --- |
| Frontend | Login, dashboard, upload flows, detail tabs, statistics, sharing pages, group workspace, admin pages |
| Backend API | Authentication, upload CRUD, sharing APIs, comments, groups, chat, admin endpoints, quota and statistics |
| Security Layer | JWT auth, admin checks, SlowAPI rate limits, file magic-number validation, input sanitization |
| Upload Access Layer | Central read-access rules for owner, direct share, group share, public visibility, and admin access |
| Collaboration Module | Direct shares, visibility toggle, comments, study groups, join requests, invites, group chat, group files |
| SM-2 Review Logic | Flashcard review scheduling and review history persistence |
| Celery Worker | Async extraction pipeline, OCR, ASR, LLM calls, upload status transitions |
| PostgreSQL | Users, uploads, summaries, concepts, flashcards, reviews, comments, shares, groups, chat, admin-visible records |
| Redis | Celery broker for asynchronous job dispatch |
| Nginx | Production-facing reverse proxy in `docker-compose.prod.yml` |

## Core Capabilities

The current implementation groups its main capabilities into the following functional areas.

### 1. Upload and Processing

- single-file and batch upload
- file-type validation and size checks
- asynchronous processing with upload status transitions
- retry for failed uploads
- course assignment and dashboard filtering

### 2. Study Asset Generation

- transcript or extracted text
- summary
- key concepts with citations
- flashcards
- upload-grounded Q&A
- knowledge graph generation
- AI learning path generation

### 3. Collaboration and Access Control

- direct sharing to a specific user
- share to study groups
- upload-level `Private` / `Public` visibility
- comments on uploaded materials
- group chat and group-shared files
- central read-access enforcement across detail, export, graph, and chat routes

### 4. Review and Analytics

- SM-2 spaced repetition review
- flashcard known-state management
- study activity heatmap
- upload and progress charts
- forgetting-curve visualization
- quota and usage summaries

### 5. Administration and Deployment

- admin dashboard for users, uploads, stats, and settings
- Docker-based local infra and production-style stack
- CI/CD workflow files under `.github/workflows`
- Windows bootstrap script for development prerequisites

## Scenario / Workflow

### Use Case: Uploading and Reviewing Study Material

This scenario is written in the style of the project proposal document, but it reflects the current codebase.

**Preconditions**

- the user is authenticated
- PostgreSQL is available
- Redis is available for normal async dispatch
- the backend can reach the Celery worker for queued processing, or fall back to in-process execution if dispatch fails immediately

**Normal flow**

1. the user opens the dashboard and uploads one file or multiple files
2. FastAPI validates extension, size, and file signature, then stores the file and creates an upload record with `Pending`
3. the backend dispatches `process_upload`
4. the worker moves the upload to `Processing`
5. text, OCR output, transcription, or video-derived content is extracted based on file type
6. the worker detects language and generates summary, concepts, and flashcards
7. generated outputs are stored in PostgreSQL and the upload becomes `Completed`
8. the user opens the upload detail page to review summary, concepts, flashcards, graph, transcript, comments, and Q&A

**Error flow**

- unsupported or invalid files are rejected before processing
- worker exceptions mark the upload as `Failed`
- failed uploads can be retried from the dashboard

**Concurrent behavior**

- while a job is processing, the user can still browse existing uploads, open completed analyses, use shared pages, or work inside study groups

**End state**

- the upload record stores transcript, language, status, and any error message
- generated study assets are persisted and available through the normal read-access rules

## Current UI Pages

The frontend currently exposes these route-level pages:

| Route | Page | Purpose |
| --- | --- | --- |
| `/login` | Login / Register | Public entry page for sign-in and account creation |
| `/` | Dashboard | Upload files, manage courses, search/filter uploads, retry failed jobs, toggle `Private` / `Public` |
| `/uploads/:id` | Upload Detail | View summary, concepts, flashcards, Q&A, graph, transcript, comments, export, and sharing controls |
| `/stats` | Statistics | Study activity, upload trends, quota overview, forgetting curve, learning path generation |
| `/shared` | Shared With Me | Open direct shares, public materials, and files shared through groups |
| `/groups` | Study Groups | Group workspace with members, invites, join requests, chat, and group-shared files |
| `/admin` | Admin Dashboard | Admin-only view for users, uploads, platform statistics, and settings |

Navigation currently shown in the authenticated navbar:

- `Dashboard`
- `Statistics`
- `Shared`
- `Groups`
- `Admin` only when `user.is_admin === true`

Important UI behavior:

- all routes except `/login` require authentication
- `/login` redirects authenticated users back to `/`
- upload detail pages become `Read Only` for non-owners even when they still have read access
- dark mode is available in the navbar

## Supported File Types

| Category | Extensions |
| --- | --- |
| Documents | `pdf`, `pptx`, `ppt`, `docx` |
| Audio | `mp3`, `wav` |
| Images | `png`, `jpg`, `jpeg` |
| Video | `mp4`, `mov` |

## AI Routing

The current runtime splits AI responsibilities by task type rather than by page.

| Capability | Current provider | Notes |
| --- | --- | --- |
| Summary generation | DeepSeek | generated from extracted upload content |
| Key concept generation | DeepSeek | includes citation-aware concept extraction |
| Flashcard generation | DeepSeek | stored for later review and SM-2 workflow |
| Upload chat | DeepSeek | user-scoped conversations grounded in upload content |
| Knowledge graph generation | DeepSeek | generated from transcript or summary-backed content |
| Learning path generation | DeepSeek | generated from completed uploads |
| Audio transcription | GLM | used for `mp3` and `wav` uploads |
| Image OCR | GLM | primary OCR path for `png`, `jpg`, `jpeg` |
| PDF OCR | GLM | primary OCR path for PDF before local fallback |
| Video extraction | GLM | combines audio transcription and sampled-frame understanding |

### Routing Notes

- DeepSeek remains the text-first reasoning and generation provider in this repository
- GLM handles media ingestion and OCR-related entry points
- PDF and image extraction still have local fallback paths when the GLM OCR path is unavailable
- the worker pipeline is responsible for calling these providers; the frontend never talks to them directly

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
