# Architecture Design Document

## 1. Overview

Smart Study Assistant is a full-stack study platform that turns uploaded materials into structured study assets:

- transcript / extracted text
- summary
- key concepts
- flashcards
- contextual Q&A
- knowledge graph
- learning path recommendations

It also supports:

- comments
- direct sharing
- public/private visibility
- study groups
- admin operations

## 2. Runtime architecture

### Core services

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind |
| API | FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Queue / broker | Celery + Redis |
| Text AI | DeepSeek |
| Media AI | GLM |

### Media routing

| Capability | Runtime provider |
|---|---|
| Summary / concepts / flashcards | DeepSeek |
| Knowledge graph | DeepSeek |
| Learning path | DeepSeek |
| Upload chat | DeepSeek |
| Audio transcription | GLM |
| Image OCR | GLM |
| PDF OCR | GLM |
| Video analysis | GLM |

### High-level flow

```text
Browser
  -> Frontend (React)
  -> FastAPI backend
      -> PostgreSQL
      -> Redis
      -> Celery worker
          -> DeepSeek
          -> GLM
```

## 3. Important runtime constraints

- Runtime database is PostgreSQL only.
- Application URLs should use `postgresql+psycopg2://...`.
- SQLite is used only in tests.
- Upload analysis depends on the Celery worker.
- In Docker, the backend and Celery worker share the same uploads volume so the worker can read uploaded files.

## 4. Backend structure

```text
backend/app/
├── api/
│   ├── auth.py
│   ├── uploads.py
│   ├── chat.py
│   ├── share.py
│   └── admin.py
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── rate_limit.py
│   ├── sanitize.py
│   └── validators.py
├── models/
├── schemas/
├── services/
│   ├── ai_service.py
│   ├── spaced_repetition.py
│   └── upload_access.py
└── workers/
    ├── celery_app.py
    └── tasks.py
```

## 5. API modules

### `auth.py`

Handles:

- register
- login
- current user
- email verification
- forgot password
- reset password

### `uploads.py`

Handles:

- single and batch upload
- upload listing
- upload detail
- export
- retry processing
- course assignment
- tags
- summary / concept / flashcard edits
- SM-2 flashcard review
- statistics
- quota
- knowledge graph
- learning path

### `chat.py`

Handles per-user conversations against one upload.

Important behavior:

- chat access is not owner-only
- users with read access to an upload can create their own conversations for that upload
- conversation records remain user-scoped

### `share.py`

Handles:

- direct shares
- public/private visibility toggle
- comments
- study groups
- group join approval
- group invites
- group messages
- group file shares

### `admin.py`

Handles:

- user list / enable / disable / delete
- platform-wide upload list
- admin share toggle on uploads
- global stats
- runtime limit settings

## 6. Upload processing pipeline

The Celery task `process_upload` is the main async job.

### Step 1: extract text

By file type:

- `pdf` -> GLM OCR first, local PDF extraction fallback
- `png/jpg/jpeg` -> GLM OCR first, local pytesseract fallback
- `pptx/ppt` -> `python-pptx`
- `docx` -> `python-docx`
- `mp3/wav` -> GLM ASR
- `mp4/mov` -> GLM ASR + sampled frame analysis

### Step 2: detect language

DeepSeek is used to infer the primary language code.

### Step 3: generate study assets

DeepSeek generates:

- summary
- key concepts
- flashcards

### Step 4: persist

The worker stores:

- upload transcript
- language
- summary row
- key concept rows
- flashcard rows

### Status lifecycle

```text
Pending -> Processing -> Completed
Pending -> Processing -> Failed
```

## 7. Access control model

### Authentication

- JWT bearer tokens
- `get_current_user` resolves the authenticated user
- `get_admin_user` enforces admin-only routes

### Upload read access

The central read-access logic lives in `services/upload_access.py`.

An upload is readable when the user is:

- the owner
- an admin
- a direct recipient of a share
- a member of a group the file was shared into
- a viewer of a file marked `is_shared=true`
- a viewer of an explicit public share record

This same logic is used by:

- upload detail
- knowledge graph
- export
- comments
- upload chat

### Owner-only operations

Still owner-only:

- delete upload
- retry upload
- edit summary
- edit concepts
- edit flashcards
- toggle upload public/private visibility
- create outgoing shares

## 8. Visibility semantics

### Upload-level visibility

`uploads.is_shared` controls whether a file is globally visible in shared materials.

- `false`: private by default
- `true`: visible to other users in shared materials

### Group sharing

If a file is private but shared to a group:

- group members can access it
- non-members cannot
- it does not become globally public

### Share records

`shared_uploads` stores:

- direct shares
- group shares
- optional public share records
- per-share `permission`

## 9. Database model summary

Main tables:

- `users`
- `courses`
- `uploads`
- `summaries`
- `key_concepts`
- `flashcards`
- `flashcard_reviews`
- `study_sessions`
- `conversations`
- `chat_messages`
- `tags`
- `shared_uploads`
- `comments`
- `study_groups`
- `group_members`
- `join_requests`
- `group_invites`
- `group_messages`

Important upload fields:

| Field | Meaning |
|---|---|
| `status` | Pending / Processing / Completed / Failed |
| `is_shared` | public visibility toggle |
| `transcript` | extracted text or transcription |
| `language` | detected language code |
| `course_id` | optional course grouping |

Important share/group fields:

| Field | Meaning |
|---|---|
| `shared_uploads.permission` | current share permission string, default `read` |
| `study_groups.join_mode` | `open` or `approval` |
| `group_members.role` | `owner` or `member` |

## 10. Frontend structure

Main routes:

| Route | Purpose |
|---|---|
| `/login` | auth |
| `/` | dashboard / upload list |
| `/uploads/:id` | upload detail |
| `/stats` | study stats |
| `/shared` | shared materials |
| `/groups` | study groups |
| `/admin` | admin console |

Key pages:

- `DashboardPage.jsx`
- `UploadDetailPage.jsx`
- `SharedPage.jsx`
- `StudyGroupPage.jsx`
- `AdminPage.jsx`

Key shared components:

- `Navbar.jsx`
- `ChatPanel.jsx`
- `KnowledgeGraph.jsx`
- `CommentSection.jsx`

## 11. Docker deployment

### `docker-compose.yml`

For local infrastructure only:

- PostgreSQL
- Redis

### `docker-compose.prod.yml`

For full production-style stack:

- PostgreSQL
- Redis
- backend
- celery worker
- frontend
- nginx

Important production detail:

- backend and worker both mount the `uploads_data` volume at `/app/uploads`

## 12. Admin model

- No default admin user is created automatically.
- Admins are regular users with `is_admin=true`.
- Admins can list all uploads from `/api/admin/uploads`.
- Admins can also open any upload detail through the normal upload detail route because upload read access explicitly allows admins.

## 13. Testing notes

Backend tests use SQLite in-memory for speed and isolation.

That test-only SQLite path does not change runtime requirements:

- local runtime: PostgreSQL
- Docker runtime: PostgreSQL
