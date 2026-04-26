from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.database import engine, Base
from app.core.rate_limit import limiter
from app.models import (  # noqa: F401
    ChatMessage,
    Comment,
    Conversation,
    Course,
    Flashcard,
    FlashcardReview,
    GroupInvite,
    GroupMember,
    GroupMessage,
    JoinRequest,
    KeyConcept,
    SharedUpload,
    StudyGroup,
    StudySession,
    Summary,
    Tag,
    Upload,
    User,
)
from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router
from app.api.admin import router as admin_router
from app.api.share import router as share_router
from app.api.chat import router as chat_router

# Create tables
Base.metadata.create_all(bind=engine)

# Add missing columns to existing tables (simple migration)
from sqlalchemy import inspect, text
with engine.connect() as conn:
    inspector = inspect(engine)
    if "study_groups" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("study_groups")]
        if "join_mode" not in columns:
            conn.execute(text("ALTER TABLE study_groups ADD COLUMN join_mode VARCHAR(20) DEFAULT 'open'"))
            conn.commit()
    if "uploads" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("uploads")]
        if "is_shared" not in columns:
            conn.execute(text("ALTER TABLE uploads ADD COLUMN is_shared BOOLEAN DEFAULT FALSE"))
            conn.commit()
        if "course_id" not in columns:
            conn.execute(text("ALTER TABLE uploads ADD COLUMN course_id INTEGER"))
            conn.commit()
    if "shared_uploads" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("shared_uploads")]
        if "permission" not in columns:
            conn.execute(text("ALTER TABLE shared_uploads ADD COLUMN permission VARCHAR(20) DEFAULT 'read'"))
            conn.commit()


app = FastAPI(title="Smart Study Assistant", version="2.0.0")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(admin_router)
app.include_router(share_router)
app.include_router(chat_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
