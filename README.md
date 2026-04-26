Here is the README enhanced with modern decorations, including badges, emojis, and visual callouts, while strictly maintaining the clean structure and information you provided:🎓 Smart Study AssistantA full-stack AI-powered learning platform built with FastAPI, React, PostgreSQL, Redis, Celery, DeepSeek, and GLM.📖 OverviewSmart Study Assistant processes learning materials, extracts content, and generates intelligent study aids including summaries, key concepts, flashcards, and knowledge graphs. It supports multi-turn Q&A, collaborative learning groups, content sharing, and administrative controls.✨ Features🧠 AI-Powered Content Analysis: Upload documents, audio, images, or videos for automatic processing.🛠️ Study Tools: Auto-generated summaries, key concepts, flashcards, knowledge graphs, and learning paths.💬 Interactive Q&A: Context-aware question answering based strictly on uploaded materials.🤝 Collaboration: Share materials, create study groups, and comment on content.📂 Multi-Format Support: Process PDF, DOCX, PPTX, MP3, WAV, PNG, JPEG, MP4, and MOV files.⚙️ Admin Dashboard: Comprehensive user management and system monitoring available at /admin.🤖 AI Model Routing📝 Text Generation (DeepSeek)SummariesKey conceptsFlashcardsKnowledge graphsLearning pathsContextual Q&A👁️ Media & OCR (GLM)Audio transcriptionImage OCRPDF OCRVideo analysis (audio + frame extraction)💻 Tech StackLayerTechnologyBackendFastAPI + SQLAlchemy + PydanticFrontendReact + Vite + Tailwind CSSDatabasePostgreSQLQueue/CacheRedis + CeleryText AIDeepSeekMedia AIGLM (Zhipu)📁 Project StructurePlaintext.
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
⚠️ Important NotesDatabase: PostgreSQL is strictly required for production. SQLite is only utilized for automated tests.SQLAlchemy URL: Must be formatted as postgresql+psycopg2://....Celery Worker: Upload processing requires an active Celery worker. If the worker is down, file uploads will hang or fail.Docker Volumes: The backend and Celery containers must share the same upload volume (this is pre-configured in the repository).🔐 Environment FilesTwo environment templates are provided:Root (.env.example): Used by Docker Compose and contains shared defaults.Backend (backend/.env.example): Used specifically for local backend development.Note: The backend loads both the root .env and backend/.env files, with backend/.env taking precedence in case of conflicts.🚀 Local Development📋 PrerequisitesPython 3.9+Node.js 16+PostgreSQL 13+Redis 6+1️⃣ Start PostgreSQL and RedisOption A: Using DockerBashdocker compose up -d postgres redis
Option B: Local PostgreSQLBashpsql -U postgres -f sql/init_postgres.sql
2️⃣ Configure Backend EnvironmentCopy the example environment file:Bash# Windows
Copy-Item backend/.env.example backend/.env

# Linux/macOS
cp backend/.env.example backend/.env
Edit backend/.env with your specific keys and credentials:代码段# Required
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
Note: AI_API_KEY serves as a fallback for DeepSeek. The primary key evaluated is DEEPSEEK_API_KEY.3️⃣ Install and Run BackendBashcd backend
python -m venv venv

# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
🟢 Backend health check: http://127.0.0.1:8000/api/health4️⃣ Start Celery WorkerWindows:Bashcd backend
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info --pool=solo
Linux/macOS:Bashcd backend
celery -A app.workers.celery_app worker --loglevel=info
5️⃣ Run FrontendBashcd frontend
npm install
npm run dev
🔵 Frontend URL: http://127.0.0.1:5173🐳 Docker Deployment🏠 Local Infrastructure OnlyUse docker-compose.yml to run only PostgreSQL and Redis. This is ideal when you want to run the FastAPI backend, Celery, and Vite directly on your local machine for active development.Bashdocker compose up -d postgres redis
🌍 Full Production StackUse docker-compose.prod.yml to spin up the complete, production-ready stack:PostgreSQLRedisFastAPI backendCelery workerReact frontendNginx reverse proxyBash# Copy and configure your root .env file first
cp .env.example .env

# Build and start the production stack
docker compose -f docker-compose.prod.yml up -d --build
👑 AdministrationAdmin Interface: Accessible at /admin.Access Control: The UI and routes are restricted to authenticated users with the is_admin=true flag.Default Admin: For security, no default admin user is seeded on startup. You must manually set is_admin=true for your user account directly in the database.🔒 File Visibility ModelPrivate: Visible only to the original owner, explicitly shared users, and members of any groups the file is shared with.Public: Visible to all registered users in the shared materials library.Private + Shared to Group: Remains restricted; only accessible to the specific group members and is not globally public.🧪 TestingBackend:Bashcd backend
pytest tests -v
Frontend:Bashcd frontend
npm test
🔧 Technical Details📄 OCR ProcessingPrimary: Utilizes GLM layout_parsing with a data URL payload for highly accurate image and PDF extraction.Fallback: Gracefully degrades to local PDF extraction or pytesseract when the GLM service is unavailable or encounters an error.📤 File UploadsProduction environments are configured to share the /app/uploads volume between the backend and Celery worker containers.This guarantees that background media processing tasks can seamlessly read and write files handled by the API.📜 LicenseMIT
