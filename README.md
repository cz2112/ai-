# 🧠 Smart Study Assistant

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![React](https://img.shields.io/badge/React-19.2-61DAFB.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

> **Course:** BSAI301 Software Engineering
> **Team:** team-10



## 📖 Project Overview (项目概览)

**Smart Study Assistant** 是一个基于 AI 的智能学习辅助平台，旨在帮助大学生解决信息过载问题。系统允许用户上传课程录音（MP3/WAV）、阅读材料（PDF）、演示文稿（PPTX）、文档（DOCX）以及图片（PNG/JPG，支持 OCR），利用大语言模型自动生成**内容摘要**、**关键知识点**以及**复习闪卡 (Flashcards)**。

平台还提供**多轮 AI 问答**、**知识图谱可视化**、**SM-2 间隔重复算法**、**AI 学习路径推荐**、**协作分享**等高级功能，通过将非结构化数据转化为结构化的复习工具，全面提升学生的复习效率和知识留存率。

### ✨ Key Features (核心功能)

- 📂 **多格式文件处理**: 支持 PDF、MP3/WAV 音频转写、PPTX/DOCX 文本提取、PNG/JPG 图片 OCR 识别，支持批量上传
- 🤖 **AI 智能分析**: 基于 Groq LLaMA 3.3 70B 自动生成摘要、关键概念与闪卡
- 💬 **多轮 AI 问答**: 基于上传材料内容的上下文对话，支持多会话管理
- 🕸️ **知识图谱**: AI 生成概念关系图，SVG 可视化展示知识结构
- 🔄 **SM-2 间隔重复**: 科学的闪卡复习调度算法（SuperMemo 2），6 级评分系统
- 🗺️ **AI 学习路径**: 根据已学内容智能推荐学习步骤与资源
- 📊 **数据可视化**: GitHub 风格学习热力图、学习进度折线图、遗忘曲线（Ebbinghaus）、状态分布饼图
- 🏷️ **标签系统**: 为上传材料添加标签，支持按标签筛选
- 👥 **协作功能**: 分享学习材料、评论讨论、创建/加入学习小组
- 🔒 **安全加固**: API 限流（SlowAPI）、文件魔数验证、输入消毒、JWT 认证、bcrypt 密码哈希
- 🛡️ **管理后台**: 用户管理、系统统计、角色控制
- ⚡ **异步处理**: Celery + Redis 架构，后台处理大型文件
- 📤 **导出功能**: 将学习笔记导出为 Markdown 格式
- 🐳 **容器化部署**: Docker Compose 生产配置、Nginx 反向代理、GitHub Actions CI/CD

---

## 🏗️ System Architecture (系统架构)

本项目采用前后端分离架构，并引入消息队列以解耦耗时的 AI 推理任务。

```mermaid
graph TD
    User([User]) -->|Browser| Client["Frontend<br/>(React 19 + Tailwind CSS v4 + Recharts)"]
    Client -->|REST API| API["Backend (FastAPI)"]

    DB[(PostgreSQL 16)]
    Redis[(Redis 7 Broker)]
    Groq["Groq LLaMA 3.3 70B"]

    subgraph Security["Security Layer"]
        RateLimit["SlowAPI Rate Limiting"]
        FileValid["File Magic Validation"]
        Sanitize["Input Sanitization"]
        JWT["JWT Authentication"]
    end

    API --> RateLimit
    API --> FileValid
    API --> Sanitize
    API --> JWT

    API -->|Read/Write| DB
    API -->|Enqueue Task| Redis

    subgraph AsyncWorker["Async Worker"]
        Worker[Celery Worker]
        Extract[Text Extraction]
        Whisper["Groq Whisper Large v3"]
    end

    Redis -->|Consume Task| Worker
    Worker -->|PDF/PPTX/DOCX/OCR| Extract
    Worker -->|Audio| Whisper
    Worker -->|Summary/Concepts/Flashcards| Groq
    Worker -->|Save Result| DB

    subgraph AIFeatures["Real-time AI Features"]
        Chat["Multi-turn Chat"]
        KGraph["Knowledge Graph"]
        LPath["Learning Path"]
        SM2["SM-2 Spaced Repetition"]
    end

    API --> Chat --> Groq
    API --> KGraph --> Groq
    API --> LPath --> Groq
    API --> SM2 --> DB

    subgraph Collaboration["Collaboration"]
        Share["Share / Comment / Groups"]
    end

    API --> Share --> DB

    subgraph Deploy["Production Deployment"]
        Nginx["Nginx Reverse Proxy"]
        Docker["Docker Compose"]
    end

    Docker --> Nginx
    Nginx --> API
    Nginx --> Client
```

---

## 🛠️ Tech Stack (技术栈)

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Python, FastAPI, SQLAlchemy, Pydantic | 3.12, 0.115, 2.0, 2.9 |
| **Frontend** | React, Vite, Tailwind CSS, Recharts | 19.2, 7.2, 4.1, 3.7 |
| **Database** | PostgreSQL, Redis | 16, 7 |
| **AI** | Groq API (LLaMA 3.3 70B, Whisper Large v3) | - |
| **Task Queue** | Celery + Redis | 5.4 |
| **Security** | JWT (python-jose), bcrypt (passlib), SlowAPI | - |
| **File Processing** | PyPDF2, python-pptx, python-docx, Pillow, pytesseract | - |
| **Testing** | pytest, pytest-asyncio, Vitest, Testing Library | - |
| **DevOps** | Docker, Nginx, GitHub Actions | - |

---

## 📁 Project Structure (项目结构)

```
smart-study-assistant/
├── backend/
│   ├── app/
│   │   ├── api/                # API 路由处理
│   │   │   ├── auth.py         # 认证 (注册/登录/个人信息)
│   │   │   ├── uploads.py      # 上传管理 (CRUD/标签/SM-2/导出)
│   │   │   ├── chat.py         # 多轮 AI 问答
│   │   │   ├── share.py        # 协作 (分享/评论/学习小组)
│   │   │   └── admin.py        # 管理后台
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 环境变量配置
│   │   │   ├── database.py     # 数据库连接
│   │   │   ├── rate_limit.py   # API 限流 (SlowAPI)
│   │   │   ├── validators.py   # 文件魔数验证
│   │   │   └── sanitize.py     # 输入消毒
│   │   ├── models/             # SQLAlchemy 数据模型 (15+ 表)
│   │   │   ├── user.py         # 用户模型
│   │   │   ├── upload.py       # 上传/摘要/闪卡/概念
│   │   │   ├── tag.py          # 标签 & 多对多关联
│   │   │   ├── conversation.py # 对话 & 消息
│   │   │   ├── study_session.py# 学习会话 & 闪卡复习记录
│   │   │   └── share.py        # 分享/评论/学习小组
│   │   ├── schemas/            # Pydantic 请求/响应模式
│   │   ├── services/           # 业务逻辑
│   │   │   ├── ai_service.py   # Groq AI 集成 (摘要/闪卡/图谱/路径)
│   │   │   └── spaced_repetition.py # SM-2 间隔重复算法
│   │   ├── workers/            # Celery 异步任务
│   │   │   └── tasks.py        # 文件处理 (PDF/音频/PPTX/DOCX/OCR)
│   │   └── main.py             # FastAPI 应用入口
│   ├── tests/                  # 后端测试套件 (7 个测试文件)
│   ├── uploads/                # 上传文件存储
│   ├── requirements.txt        # Python 依赖
│   └── Dockerfile              # 后端 Docker 镜像
├── frontend/
│   ├── src/
│   │   ├── components/         # 可复用组件
│   │   │   ├── Navbar.jsx      # 导航栏
│   │   │   ├── ChatPanel.jsx   # 多轮 AI 问答面板
│   │   │   ├── KnowledgeGraph.jsx # 知识图谱 SVG 可视化
│   │   │   ├── StudyHeatmap.jsx   # GitHub 风格学习热力图
│   │   │   └── CommentSection.jsx # 评论区组件
│   │   ├── contexts/           # React Context (Auth, Theme)
│   │   ├── pages/              # 页面组件
│   │   │   ├── LoginPage.jsx   # 登录/注册
│   │   │   ├── DashboardPage.jsx  # 仪表盘 (上传/批量/标签)
│   │   │   ├── UploadDetailPage.jsx # 详情 (6 Tab: 摘要/概念/闪卡/Q&A/图谱/文本)
│   │   │   ├── StatsPage.jsx   # 统计 (热力图/进度/遗忘曲线/学习路径)
│   │   │   ├── SharedPage.jsx  # 共享材料
│   │   │   ├── StudyGroupPage.jsx # 学习小组
│   │   │   └── AdminPage.jsx   # 管理后台
│   │   ├── services/           # API 客户端
│   │   ├── __tests__/          # 前端测试套件
│   │   └── App.jsx             # 根组件 & 路由
│   ├── vitest.config.js        # Vitest 测试配置
│   ├── package.json            # Node.js 依赖
│   └── Dockerfile              # 前端 Docker 镜像
├── nginx/
│   └── nginx.conf              # Nginx 反向代理配置
├── docs/
│   ├── API.md                  # API 接口文档
│   ├── ARCHITECTURE.md         # 架构设计文档
│   └── USER_GUIDE.md           # 用户手册
├── .github/workflows/
│   ├── ci.yml                  # CI 流水线 (测试/构建/Lint)
│   └── deploy.yml              # 部署工作流
├── docker-compose.prod.yml     # 生产环境 Docker Compose
├── .env.example                # 环境变量模板
└── README.md
```

---

## 🗄️ Database Schema (数据库设计)

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `users` | 用户账户 | username, email, password_hash, is_admin |
| `courses` | 课程分类 | name, user_id |
| `uploads` | 上传文件 | filename, file_type, status, transcript |
| `summaries` | AI 摘要 | content, upload_id |
| `key_concepts` | 关键概念 | title, description, citation |
| `flashcards` | 闪卡 | question, answer, is_known |
| `tags` | 标签 | name, user_id |
| `upload_tags` | 上传-标签关联 | upload_id, tag_id |
| `conversations` | 对话会话 | upload_id, user_id, title |
| `messages` | 对话消息 | role, content, conversation_id |
| `study_sessions` | 学习活动记录 | activity_type, duration_seconds |
| `flashcard_reviews` | SM-2 复习记录 | quality, easiness, interval_days, next_review |
| `shared_uploads` | 分享记录 | upload_id, shared_with_id, permission |
| `comments` | 评论 | content, upload_id, user_id |
| `study_groups` | 学习小组 | name, description, owner_id |
| `group_members` | 小组成员 | group_id, user_id, role |

---

## 🚀 Quick Start (快速开始)

### Prerequisites (前置要求)

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose (生产部署)

### Development Setup (开发环境)

**1. 克隆仓库**

```bash
git clone <repo-url>
cd smart-study-assistant
```

**2. 配置环境变量**

```bash
cp .env.example backend/.env
```

编辑 `backend/.env`：

```env
DATABASE_URL=postgresql://studyapp:studyapp123@localhost:5432/smart_study
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-in-production
GROQ_API_KEY=your-groq-api-key
```

**3. 启动后端**

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**4. 启动 Celery Worker**

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

**5. 启动前端**

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

### Production Deployment (生产部署)

```bash
cp .env.example .env
# 编辑 .env 填入生产环境配置
docker compose -f docker-compose.prod.yml up -d
```

生产环境包含 6 个服务：PostgreSQL、Redis、FastAPI 后端、Celery Worker、React 前端、Nginx 反向代理。

---

## 🧪 Testing (测试)

### 后端测试 (pytest)

```bash
cd backend
pytest tests/ -v
```

测试覆盖：认证 API、上传 API、管理员 API、聊天 API、协作 API、SM-2 算法单元测试。

### 前端测试 (Vitest)

```bash
cd frontend
npm test
```

测试覆盖：LoginPage、DashboardPage、Navbar 组件测试。

---

## 📡 API Endpoints (API 接口概览)

| 模块 | 端点数 | 主要功能 |
|------|--------|---------|
| **Auth** `/api/auth` | 3 | 注册、登录、获取个人信息 |
| **Uploads** `/api/uploads` | 25+ | 文件上传/批量上传、CRUD、标签管理、SM-2 复习、知识图谱、学习路径、学习会话 |
| **Chat** `/api/chat` | 4 | 多轮对话、会话管理 |
| **Share** `/api/share` | 12 | 分享材料、评论、学习小组 CRUD |
| **Admin** `/api/admin` | 5+ | 用户管理、系统统计 |

详细文档见 [API Documentation](docs/API.md)。

---

## 📚 Documentation (文档)

- 📘 [API 接口文档](docs/API.md) — 所有端点的详细请求/响应格式
- 🏛️ [架构设计文档](docs/ARCHITECTURE.md) — 系统架构、数据库设计、安全策略
- 📖 [用户手册](docs/USER_GUIDE.md) — 功能使用指南

---

## 👥 Team (团队)

4 人开发团队，学期课程项目。

---

## 📄 License

MIT
