# Smart Study Assistant

A full-stack AI-powered learning platform built with FastAPI, React, PostgreSQL, Redis, Celery, DeepSeek, and GLM.

## Overview

Smart Study Assistant processes learning materials, extracts content, and generates intelligent study aids including summaries, key concepts, flashcards, and knowledge graphs. It supports multi-turn Q&A, collaborative learning groups, content sharing, and administrative controls.

## Features

- **AI-Powered Content Analysis**: Upload documents, audio, images, or videos for automatic processing
- **Study Tools**: Auto-generated summaries, key concepts, flashcards, knowledge graphs, and learning paths
- **Interactive Q&A**: Context-aware question answering based on uploaded materials
- **Collaboration**: Share materials, create study groups, and comment on content
- **Multi-Format Support**: PDF, DOCX, PPTX, MP3, WAV, PNG, JPEG, MP4, MOV
- **Admin Dashboard**: User management and system monitoring at `/admin`

## AI Model Routing

### Text Generation (DeepSeek)
- Summaries
- Key concepts
- Flashcards
- Knowledge graphs
- Learning paths
- Contextual Q&A

### Media & OCR (GLM)
- Audio transcription
- Image OCR
- PDF OCR
- Video analysis (audio + frame extraction)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + SQLAlchemy + Pydantic |
| Frontend | React + Vite + Tailwind CSS |
| Database | PostgreSQL |
| Queue/Cache | Redis + Celery |
| Text AI | DeepSeek |
| Media AI | GLM (Zhipu) |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── workers/      # Celery tasks
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── nginx/
├── sql/
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## Important Notes

- **Database**: PostgreSQL is required for production. SQLite is only used for automated tests.
- **SQLAlchemy URL**: Must use `postgresql+psycopg2://...` format.
- **Celery Worker**: Upload processing requires a running Celery worker. If the worker is down, uploads will hang or fail.
- **Docker Volumes**: Backend and Celery containers must share the same upload volume (pre-configured in this repo).

## Environment Files

Two environment templates are provided:

1. **Root**: `.env.example` - Used by Docker Compose and shared defaults
2. **Backend**: `backend/.env.example` - Used for local backend development

The backend loads both root `.env` and `backend/.env`, with `backend/.env` taking precedence.

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### 1. Start PostgreSQL and Redis

**Option A: Using Docker**
```bash
docker compose up -d postgres redis
```

**Option B: Local PostgreSQL**
```bash
psql -U postgres -f sql/init_postgres.sql
```

### 2. Configure Backend Environment

```bash
Copy-Item backend/.env.example backend/.env
```

Edit `backend/.env` with required values:

```env
# Required
DATABASE_URL=postgresql+psycopg2://studyapp:studyapp123@localhost:5432/smart_study
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production

# DeepSeek (Text AI)
DEEPSEEK_API_KEY=your-deepseek-key
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash

# GLM (Media AI)
ZHIPU_API_KEY=your-glm-key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_ASR_MODEL=glm-asr-2512
GLM_VISION_MODEL=glm-4.6v
GLM_OCR_MODEL=glm-ocr

# Optional: Email (for verification and password reset)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=465
MAIL_SERVER=smtp.qq.com
```

**Note**: `AI_API_KEY` is a fallback for DeepSeek. The primary key is `DEEPSEEK_API_KEY`.

### 3. Install and Run Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend health check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 4. Start Celery Worker

**Windows:**
```bash
cd backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info --pool=solo
```

**Linux/Mac:**
```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info
```

### 5. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Docker Deployment

### Local Infrastructure Only

Use `docker-compose.yml` to run only PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

This is useful when you want to run FastAPI/Celery/Vite directly on your machine but keep databases in containers.

### Full Production Stack

Use `docker-compose.prod.yml` to run the complete stack:

- PostgreSQL
- Redis
- FastAPI backend
- Celery worker
- React frontend
- Nginx reverse proxy

```bash
Copy-Item .env.example .env
# Edit .env with your configuration
docker compose -f docker-compose.prod.yml up -d --build
```

## Administration

- **Admin Interface**: `/admin`
- **Access**: Only visible to authenticated users with `is_admin=true`
- **Default Admin**: No default admin user is created on startup. You must manually set `is_admin=true` in the database.

## File Visibility Model

### Private
- Visible to owner
- Visible to explicitly shared users
- Visible to members of groups the file is shared with

### Public
- Visible in shared materials list to all users

### Private + Shared to Group
- Only accessible to group members
- Not publicly visible

## Testing

**Backend:**
```bash
cd backend
pytest tests -v
```

**Frontend:**
```bash
cd frontend
npm test
```

## Technical Details

### OCR Processing
- Primary: GLM `layout_parsing` with data URL payload for images and PDFs
- Fallback: Local PDF extraction or `pytesseract` when GLM is unavailable

### File Uploads
- Production environments share `/app/uploads` between backend and worker containers
- Ensures media processing can correctly read uploaded files

## License

MIT
