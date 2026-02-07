# Architecture Design Document

## 1. System Overview

Smart Study Assistant is an AI-powered learning platform that transforms raw study
materials into structured, interactive learning resources. The system supports the
following core workflows:

- **Material Upload and Processing**: Users upload study materials in various formats
  (PDF, audio MP3/WAV, PPTX, DOCX, images PNG/JPG). A background worker extracts
  text content and sends it to an AI model, which generates summaries, flashcards,
  and key concepts with citations automatically.
- **Multi-turn Q&A Chat**: Users can ask questions about any uploaded document in a
  conversational interface. The AI answers based on the document context, maintaining
  full conversation history across multiple turns.
- **Knowledge Graph**: AI extracts entities and relationships from study materials and
  presents them as an interactive node-and-edge graph for visual learning.
- **Learning Paths**: The system analyzes a student's uploaded materials and known
  concepts to suggest a personalized, ordered learning path.
- **Spaced Repetition (SM-2)**: Flashcard reviews follow the SuperMemo SM-2 algorithm,
  scheduling cards at increasing intervals based on recall quality (0-5 scale).
- **Collaboration**: Users can share uploads publicly or with specific users, leave
  comments on shared materials, and form study groups with member management.
- **Admin Dashboard**: Administrators can manage users (activate, deactivate, promote)
  and view platform-wide statistics.

---

## 2. Technology Stack

### Backend

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Language        | Python 3.12                         |
| Web Framework   | FastAPI                             |
| ORM             | SQLAlchemy (declarative base)       |
| Database        | PostgreSQL 16 (Alpine)              |
| Cache / Broker  | Redis 7 (Alpine)                    |
| Task Queue      | Celery                              |
| Auth            | python-jose (JWT), passlib (bcrypt) |
| Rate Limiting   | SlowAPI                             |
| Settings        | pydantic-settings (BaseSettings)    |
| AI Client       | Groq Python SDK                     |
| PDF Parsing     | PyPDF2                              |
| PPTX Parsing    | python-pptx                         |
| DOCX Parsing    | python-docx                         |
| OCR             | pytesseract + Pillow                |

### Frontend

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Library         | React 19                            |
| Build Tool      | Vite 7                              |
| CSS Framework   | Tailwind CSS v4                     |
| Charts          | Recharts 3                          |
| HTTP Client     | Axios                               |
| Routing         | React Router v7                     |
| Testing         | Vitest, Testing Library             |
| Linting         | ESLint 9                            |

### AI Services

| Capability          | Model                               |
|---------------------|-------------------------------------|
| Text Generation     | Groq API -- llama-3.3-70b-versatile |
| Audio Transcription | Groq API -- whisper-large-v3        |

### Infrastructure

| Component        | Technology                          |
|------------------|-------------------------------------|
| Containerization | Docker, Docker Compose              |
| Reverse Proxy    | Nginx (Alpine)                      |
| CI/CD            | GitHub Actions                      |

---

## 3. System Architecture Diagram

```
+-------------------+
|     Browser       |
| (React 19 + Vite) |
+--------+----------+
         |
         | HTTP / WebSocket
         v
+--------+----------+
|      Nginx        |
|  (reverse proxy)  |
|  port 80          |
+---+----------+----+
    |          |
    |          |
    v          v
+---+---+  +--+------------+       +------------------+
|Frontend|  |   Backend     |       |  Celery Worker   |
| (React)|  |  (FastAPI)    +------>+  (async tasks)   |
| static |  |  port 8000    |       +--------+---------+
+--------+  +--+-----+------+                |
               |     |                       |
               v     v                       v
        +------++ +--+------+       +--------+---------+
        |Postgres| |  Redis  |       |    Groq API      |
        |  :5432 | |  :6379  |       | (LLM + Whisper)  |
        +--------+ +---------+       +------------------+
```

**Request flow:**

1. The browser sends all requests to Nginx on port 80.
2. Nginx routes `/api/*` and `/ws/*` paths to the FastAPI backend on port 8000.
3. All other paths (`/`) are forwarded to the frontend static server.
4. The backend reads and writes data to PostgreSQL via SQLAlchemy.
5. File processing tasks are dispatched to Celery via Redis as the message broker.
6. The Celery worker calls the Groq API for AI operations (text generation,
   audio transcription) and writes results back to PostgreSQL.

---

## 4. Backend Architecture

The backend follows a layered architecture with clear separation of concerns:

```
backend/app/
  main.py              # FastAPI application entry point
  api/                 # API route handlers (controllers)
    auth.py            # Authentication endpoints (register, login)
    uploads.py         # File upload and processing endpoints
    chat.py            # Multi-turn Q&A chat endpoints
    share.py           # Sharing, comments, study groups endpoints
    admin.py           # Admin user management endpoints
  models/              # SQLAlchemy ORM models
    user.py            # User model
    course.py          # Course model
    upload.py          # Upload model
    study_material.py  # Summary, KeyConcept, Flashcard models
    tag.py             # Tag model and upload_tags association table
    conversation.py    # Conversation and Message models
    study_session.py   # StudySession and FlashcardReview models
    share.py           # SharedUpload, Comment, StudyGroup, GroupMember
  services/            # Business logic layer
    ai_service.py      # Groq API integration (LLM + Whisper)
    spaced_repetition.py  # SM-2 algorithm implementation
  core/                # Cross-cutting concerns
    config.py          # Application settings (pydantic-settings)
    database.py        # SQLAlchemy engine, session, Base
    security.py        # JWT creation/validation, password hashing
    rate_limit.py      # SlowAPI rate limiter instance
    validators.py      # File MIME type and magic byte validation
    sanitize.py        # Input sanitization and validation helpers
  workers/             # Asynchronous task processing
    celery_app.py      # Celery application configuration
    tasks.py           # Background task definitions
  schemas/             # Pydantic request/response schemas
```

### 4.1 API Layer

The API layer is organized into five router modules, all mounted under the `/api` prefix:

- **auth** (`/api/auth`): User registration and login. Returns JWT access tokens.
- **uploads** (`/api/uploads`): File upload with validation, retrieval of processed
  materials (summaries, flashcards, key concepts), knowledge graph generation,
  learning path generation, and spaced repetition review endpoints.
- **chat** (`/api/chat`): Create conversations tied to uploads, send messages, and
  receive AI-generated responses with full document context.
- **share** (`/api/share`): Share uploads with other users or publicly, manage
  comments on shared materials, create and manage study groups.
- **admin** (`/api/admin`): User listing, activation/deactivation, and role management.
  Protected by admin-only authorization.

### 4.2 Service Layer

- **ai_service**: Central integration point with the Groq API. Provides functions for:
  - Text extraction from multiple formats (PDF via PyPDF2, PPTX via python-pptx,
    DOCX via python-docx, images via pytesseract OCR)
  - Audio transcription via Whisper (whisper-large-v3)
  - Language detection
  - Summary generation (200-400 words)
  - Key concept extraction with citations (5-10 concepts per document)
  - Flashcard generation (8-15 Q&A pairs per document)
  - Knowledge graph extraction (15-25 nodes with labeled edges)
  - Learning path generation (5-8 ordered steps)
  - Multi-turn contextual chat
  - Multi-language support (English, Chinese, Japanese, Korean, and others)

- **spaced_repetition**: Implements the SuperMemo SM-2 algorithm. Given a quality
  rating (0-5), current repetition count, easiness factor, and interval, it computes
  the next review date. Correct responses (quality >= 3) increase the interval
  exponentially; incorrect responses reset to day 1.

### 4.3 Worker Layer

Celery is configured with Redis as both broker and result backend. The primary task is
`process_upload`, which runs the full processing pipeline for an uploaded file:

1. Extract text content based on file type
2. Detect the document language
3. Generate an AI summary
4. Extract key concepts with citations
5. Generate flashcards

The task includes retry logic (up to 2 retries with a 30-second delay) and updates the
upload status through the lifecycle: `Pending` -> `Processing` -> `Completed` or `Failed`.

---

## 5. Database Schema

The application uses PostgreSQL with 16 tables (15 named tables plus 1 association table).
All models inherit from SQLAlchemy's `declarative_base()`.

### Entity Relationship Overview

```
users ──< courses
users ──< uploads ──< summaries       (1:1)
                  ──< key_concepts     (1:N)
                  ──< flashcards       (1:N)
                  ──< conversations ──< messages
                  >──< tags            (M:N via upload_tags)

users ──< study_sessions
users ──< flashcard_reviews
flashcards ──< flashcard_reviews

users ──< shared_uploads (as shared_by)
users ──< shared_uploads (as shared_with)
uploads ──< shared_uploads
uploads ──< comments
users ──< comments

users ──< study_groups (as owner)
study_groups ──< group_members
users ──< group_members
study_groups ──< shared_uploads
```

### Table Details

#### users
| Column          | Type         | Constraints                    |
|-----------------|--------------|--------------------------------|
| id              | Integer      | PK, auto-increment             |
| username        | String(50)   | Unique, indexed, not null       |
| email           | String(100)  | Unique, indexed, not null       |
| hashed_password | String(255)  | Not null                        |
| is_admin        | Boolean      | Default: false                  |
| is_active       | Boolean      | Default: true                   |
| created_at      | DateTime     | Default: UTC now                |

#### courses
| Column     | Type        | Constraints                     |
|------------|-------------|---------------------------------|
| id         | Integer     | PK, auto-increment              |
| user_id    | Integer     | FK -> users.id, not null        |
| name       | String(100) | Not null                        |
| created_at | DateTime    | Default: UTC now                |

#### uploads
| Column        | Type        | Constraints                      |
|---------------|-------------|----------------------------------|
| id            | Integer     | PK, auto-increment               |
| user_id       | Integer     | FK -> users.id, not null         |
| course_id     | Integer     | FK -> courses.id, nullable       |
| filename      | String(255) | Not null                         |
| file_type     | String(10)  | Not null (pdf/mp3/wav/pptx/docx/png/jpg) |
| file_path     | String(500) | Not null                         |
| file_size     | Integer     | Default: 0                       |
| status        | String(20)  | Default: "Pending"               |
| error_message | Text        | Nullable                         |
| transcript    | Text        | Nullable                         |
| language      | String(10)  | Default: "en"                    |
| created_at    | DateTime    | Default: UTC now                 |
| updated_at    | DateTime    | Default: UTC now, auto-update    |

#### summaries
| Column     | Type    | Constraints                          |
|------------|---------|--------------------------------------|
| id         | Integer | PK, auto-increment                   |
| upload_id  | Integer | FK -> uploads.id, unique, not null   |
| content    | Text    | Not null                             |
| created_at | DateTime| Default: UTC now                     |

#### key_concepts
| Column      | Type        | Constraints                     |
|-------------|-------------|---------------------------------|
| id          | Integer     | PK, auto-increment              |
| upload_id   | Integer     | FK -> uploads.id, not null      |
| title       | String(255) | Not null                        |
| description | Text        | Not null                        |
| citation    | Text        | Nullable                        |
| created_at  | DateTime    | Default: UTC now                |

#### flashcards
| Column     | Type    | Constraints                         |
|------------|---------|-------------------------------------|
| id         | Integer | PK, auto-increment                  |
| upload_id  | Integer | FK -> uploads.id, not null          |
| question   | Text    | Not null                            |
| answer     | Text    | Not null                            |
| is_known   | Boolean | Default: false                      |
| created_at | DateTime| Default: UTC now                    |

#### tags
| Column  | Type       | Constraints                        |
|---------|------------|------------------------------------|
| id      | Integer    | PK, auto-increment                 |
| user_id | Integer    | FK -> users.id, not null           |
| name    | String(50) | Not null                           |

#### upload_tags (association table)
| Column    | Type    | Constraints                                  |
|-----------|---------|----------------------------------------------|
| upload_id | Integer | PK, FK -> uploads.id (CASCADE on delete)     |
| tag_id    | Integer | PK, FK -> tags.id (CASCADE on delete)        |

#### conversations
| Column     | Type        | Constraints                     |
|------------|-------------|---------------------------------|
| id         | Integer     | PK, auto-increment              |
| user_id    | Integer     | FK -> users.id, not null        |
| upload_id  | Integer     | FK -> uploads.id, not null      |
| title      | String(255) | Default: "New Chat"             |
| created_at | DateTime    | Default: UTC now                |

#### messages
| Column          | Type       | Constraints                      |
|-----------------|------------|----------------------------------|
| id              | Integer    | PK, auto-increment               |
| conversation_id | Integer    | FK -> conversations.id, not null |
| role            | String(20) | Not null ("user" or "assistant") |
| content         | Text       | Not null                         |
| created_at      | DateTime   | Default: UTC now                 |

#### study_sessions
| Column           | Type       | Constraints                     |
|------------------|------------|---------------------------------|
| id               | Integer    | PK, auto-increment              |
| user_id          | Integer    | FK -> users.id, not null        |
| upload_id        | Integer    | FK -> uploads.id, nullable      |
| activity_type    | String(50) | Not null                        |
| cards_reviewed   | Integer    | Default: 0                      |
| cards_known      | Integer    | Default: 0                      |
| duration_seconds | Integer    | Default: 0                      |
| created_at       | DateTime   | Default: UTC now                |

#### flashcard_reviews
| Column        | Type     | Constraints                        |
|---------------|----------|------------------------------------|
| id            | Integer  | PK, auto-increment                 |
| flashcard_id  | Integer  | FK -> flashcards.id, not null      |
| user_id       | Integer  | FK -> users.id, not null           |
| quality       | Integer  | Not null (0-5, SM-2 scale)         |
| easiness      | Float    | Default: 2.5                       |
| interval_days | Integer  | Default: 1                         |
| repetitions   | Integer  | Default: 0                         |
| next_review   | DateTime | Not null                           |
| reviewed_at   | DateTime | Default: UTC now                   |

#### shared_uploads
| Column      | Type    | Constraints                          |
|-------------|---------|--------------------------------------|
| id          | Integer | PK, auto-increment                   |
| upload_id   | Integer | FK -> uploads.id, not null           |
| shared_by   | Integer | FK -> users.id, not null             |
| shared_with | Integer | FK -> users.id, nullable (null=public)|
| group_id    | Integer | FK -> study_groups.id, nullable      |
| message     | Text    | Nullable                             |
| created_at  | DateTime| Default: UTC now                     |

#### comments
| Column     | Type    | Constraints                         |
|------------|---------|-------------------------------------|
| id         | Integer | PK, auto-increment                  |
| upload_id  | Integer | FK -> uploads.id, not null          |
| user_id    | Integer | FK -> users.id, not null            |
| content    | Text    | Not null                            |
| created_at | DateTime| Default: UTC now                    |

#### study_groups
| Column      | Type        | Constraints                     |
|-------------|-------------|---------------------------------|
| id          | Integer     | PK, auto-increment              |
| name        | String(100) | Not null                        |
| description | Text        | Nullable                        |
| owner_id    | Integer     | FK -> users.id, not null        |
| created_at  | DateTime    | Default: UTC now                |

#### group_members
| Column    | Type       | Constraints                        |
|-----------|------------|------------------------------------|
| id        | Integer    | PK, auto-increment                 |
| group_id  | Integer    | FK -> study_groups.id, not null    |
| user_id   | Integer    | FK -> users.id, not null           |
| role      | String(20) | Default: "member"                  |
| joined_at | DateTime   | Default: UTC now                   |

---

## 6. Frontend Architecture

The frontend is a single-page application built with React 19 and bundled by Vite 7.

### 6.1 Page Components

| Route            | Component        | Description                              |
|------------------|------------------|------------------------------------------|
| `/login`         | LoginPage        | User registration and login forms        |
| `/`              | DashboardPage    | Main dashboard with upload list and stats |
| `/uploads/:id`   | UploadDetailPage | View summary, flashcards, concepts, chat |
| `/stats`         | StatsPage        | Study statistics and heatmap             |
| `/admin`         | AdminPage        | Admin user management panel              |
| `/shared`        | SharedPage       | Browse shared materials                  |
| `/groups`        | StudyGroupPage   | Study group management                   |

All routes except `/login` are wrapped in a `PrivateRoute` component that checks
authentication state and redirects unauthenticated users to the login page.

### 6.2 Shared Components

| Component       | Purpose                                              |
|-----------------|------------------------------------------------------|
| Navbar          | Top navigation bar with links and user menu          |
| ChatPanel       | Multi-turn Q&A chat interface for document questions  |
| KnowledgeGraph  | Interactive node-and-edge visualization of concepts   |
| StudyHeatmap    | Calendar heatmap showing daily study activity         |
| CommentSection  | Threaded comments on shared uploads                   |

### 6.3 State Management

- **AuthContext**: Manages user authentication state (current user, JWT token,
  login/logout functions). Wraps the entire application.
- **ThemeContext**: Manages light/dark theme preference. Wraps the entire application
  inside AuthContext.
- **Local State**: Individual components use React hooks (`useState`, `useEffect`)
  for component-level state. No global state library is used.

### 6.4 Routing

React Router v7 is used for client-side routing. The `BrowserRouter` wraps all routes,
and the `PrivateRoute` higher-order component enforces authentication:

```jsx
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" />;
}
```

---

## 7. Security

### 7.1 Authentication

- **JWT Tokens**: Users authenticate via username/password and receive a JWT access
  token signed with HS256. Tokens expire after 24 hours (configurable via
  `ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Password Hashing**: All passwords are hashed using bcrypt via the `passlib` library.
  Plaintext passwords are never stored.
- **OAuth2 Bearer**: The FastAPI `OAuth2PasswordBearer` scheme extracts tokens from
  the `Authorization: Bearer <token>` header.

### 7.2 Authorization

- **Role-based Access**: The `get_admin_user` dependency enforces admin-only access
  on admin endpoints, returning HTTP 403 for non-admin users.
- **Resource Ownership**: API endpoints verify that users can only access their own
  uploads, conversations, and other resources.

### 7.3 Rate Limiting

- SlowAPI is integrated at the application level using `get_remote_address` as the
  key function. Rate limit exceeded responses are handled by a custom exception handler.

### 7.4 File Upload Security

- **MIME Type Validation**: Uploaded files are checked against a whitelist of allowed
  MIME types per file extension.
- **Magic Byte Validation**: File content is verified against known magic byte
  signatures (e.g., `%PDF` for PDF, `\x89PNG` for PNG, `PK\x03\x04` for PPTX/DOCX)
  to prevent extension spoofing.
- **Size Limits**: Maximum upload size is 50 MB (configurable). Audio files are limited
  to 60 minutes, and PDFs to 200 pages.
- **Per-user Limits**: Each user is limited to 50 uploads.

### 7.5 Input Sanitization

- HTML tags are stripped from user input using regex.
- Special characters are escaped via `html.escape()`.
- String length is enforced (default 500 characters).
- Usernames are validated against `^[a-zA-Z0-9_]{3,50}$`.
- Email addresses are validated with a regex pattern and limited to 100 characters.

### 7.6 CORS

CORS middleware is configured to allow requests from the development origins
(`http://localhost:5173` and `http://localhost:3000`) with credentials, all methods,
and all headers.

---

## 8. Deployment

### 8.1 Docker Compose Services

The production deployment uses Docker Compose with six services:

| Service        | Image / Build       | Port  | Purpose                          |
|----------------|---------------------|-------|----------------------------------|
| db             | postgres:16-alpine  | 5432  | Primary database                 |
| redis          | redis:7-alpine      | 6379  | Message broker and cache         |
| backend        | ./backend (build)   | 8000  | FastAPI application server       |
| celery_worker  | ./backend (build)   | --    | Async task processing            |
| frontend       | ./frontend (build)  | --    | React static file server         |
| nginx          | nginx:alpine        | 80    | Reverse proxy (public entry)     |

Service dependencies are enforced with health checks:
- `backend` and `celery_worker` wait for `db` and `redis` to be healthy.
- `nginx` waits for `backend` and `frontend` to be available.

### 8.2 Nginx Configuration

Nginx listens on port 80 and routes traffic as follows:
- `/api/*` -> FastAPI backend (port 8000)
- `/ws/*` -> FastAPI backend with WebSocket upgrade headers
- `/*` -> Frontend static server

The `client_max_body_size` is set to 50M to match the backend upload limit.

### 8.3 CI/CD Pipeline

GitHub Actions runs two workflow files:

**CI (`ci.yml`)** -- Triggered on push to `main`/`develop` and pull requests to `main`:
- **backend-test**: Spins up a PostgreSQL 16 service, installs Python 3.12 dependencies,
  and runs `pytest tests/ -v`.
- **frontend-test**: Installs Node.js 20 dependencies, runs `npm test`, and verifies
  the production build with `npm run build`.
- **lint**: Runs ESLint on the frontend code.

**Deploy (`deploy.yml`)** -- Triggered on push to `main`:
- Builds all Docker images using `docker-compose.prod.yml`.
- Placeholder deploy step (to be configured per hosting provider).

### 8.4 Environment Variables

The application is configured via environment variables (loaded from `.env` in development):

| Variable                    | Default                              | Description                    |
|-----------------------------|--------------------------------------|--------------------------------|
| `DATABASE_URL`              | postgresql://studyapp:...@localhost  | PostgreSQL connection string   |
| `REDIS_URL`                 | redis://localhost:6379/0             | Redis connection string        |
| `GROQ_API_KEY`              | (empty)                              | Groq API key for AI services   |
| `SECRET_KEY`                | change-this-to-a-random-secret-key   | JWT signing secret             |
| `ACCESS_TOKEN_EXPIRE_MINUTES`| 1440 (24 hours)                     | JWT token lifetime             |
| `UPLOAD_DIR`                | ./uploads                            | File storage directory         |
| `MAX_UPLOAD_SIZE_MB`        | 50                                   | Maximum file upload size       |
| `MAX_UPLOADS_PER_USER`      | 50                                   | Per-user upload limit          |
| `MAX_AUDIO_MINUTES`         | 60                                   | Maximum audio file duration    |
| `MAX_PDF_PAGES`             | 200                                  | Maximum PDF page count         |