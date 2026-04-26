这里为您提供另一个版本的 README。这个版本采用了极简、面向开发者（Developer-focused）的风格，去除了多余的修饰，将核心重点放在了快速启动（Quickstart）和架构逻辑上，非常适合放在 GitHub 仓库中供其他工程师快速阅读。

Smart Study Assistant
A full-stack, AI-native learning platform. It ingests documents, audio, and video to automatically generate study materials (summaries, flashcards, knowledge graphs) and enables contextual Q&A using DeepSeek and Zhipu GLM.

💡 Core Capabilities
Multimodal Ingestion: Process Text (PDF, DOCX, PPTX), Media (MP4, MOV, MP3, WAV), and Images (PNG, JPEG).

AI Study Tools: Auto-generation of Summaries, Key Concepts, Flashcards, and Learning Paths.

Contextual Q&A: RAG-style multi-turn chatting based strictly on uploaded materials.

Collaboration: Private materials, public sharing, and dedicated Study Groups.

Advanced OCR & ASR: Powered by GLM layout_parsing with local fallbacks (pytesseract).

🏗 Architecture
Frontend: React + Vite + Tailwind CSS

Backend: FastAPI + SQLAlchemy + Pydantic

Database: PostgreSQL (Primary) + Redis (Cache/Message Broker)

Async Queue: Celery (crucial for heavy media/AI processing)

AI Routing:

DeepSeek (deepseek-v4-flash): Text generation, reasoning, Q&A.

Zhipu GLM (glm-4.6v, glm-ocr, glm-asr): OCR, vision, audio transcription.

🚀 Quick Start (Local Development)
1. Spin up Infrastructure
Run the database and cache using the provided docker-compose:

Bash
docker compose up -d postgres redis
2. Configure Environment
Copy the environment templates:

Bash
cp .env.example .env
cp backend/.env.example backend/.env
Note: The backend loads both, but backend/.env takes precedence. You must populate DEEPSEEK_API_KEY and ZHIPU_API_KEY.

3. Start Backend API
Bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
API Health Check: http://127.0.0.1:8000/api/health

4. Start Celery Worker
⚠️ Important: Uploads will hang if the worker is not running.

Bash
cd backend
# Linux/macOS
celery -A app.workers.celery_app worker --loglevel=info
# Windows
.\venv\Scripts\celery.exe -A app.workers.celery_app worker --loglevel=info --pool=solo
5. Start Frontend
Bash
cd frontend
npm install
npm run dev
App URL: http://127.0.0.1:5173

🐳 Production Deployment
For a full production rollout (FastAPI, React, Celery, Postgres, Redis, and Nginx reverse proxy):

Bash
cp .env.example .env
# Edit .env with your production secrets
docker compose -f docker-compose.prod.yml up -d --build
Note on Docker Volumes: The /app/uploads volume is shared between the API and Celery worker containers to ensure seamless file processing.

🔐 Authorization & Access
File Visibility Model
Private: Owner only.

Shared to Group: Accessible only to members of the specific study group.

Public: Visible to all registered users in the shared library.

Admin Dashboard
Route: /admin

Access: Requires is_admin=true in the database.

Setup: No default admin is seeded. You must manually set your first user's is_admin flag to true directly in PostgreSQL.

🧪 Testing
Backend: cd backend && pytest tests -v (Uses SQLite exclusively for testing)

Frontend: cd frontend && npm test
