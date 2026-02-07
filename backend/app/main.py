from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.database import engine, Base
from app.core.rate_limit import limiter
from app.models import User, Course, Upload, Summary, KeyConcept, Flashcard  # noqa: F401
from app.models.tag import Tag  # noqa: F401
from app.models.conversation import Conversation, Message  # noqa: F401
from app.models.study_session import StudySession, FlashcardReview  # noqa: F401
from app.models.share import SharedUpload, Comment, StudyGroup, GroupMember, JoinRequest, GroupInvite, GroupMessage  # noqa: F401
from app.api.auth import router as auth_router
from app.api.uploads import router as uploads_router
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.share import router as share_router

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


# Seed default admin user
def _seed_admin():
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                email="admin@smart-study.local",
                hashed_password=hash_password("admin123"),
                is_admin=True,
            ))
            db.commit()
            print("[seed] Admin user created: admin / admin123")
    finally:
        db.close()


_seed_admin()

app = FastAPI(title="Smart Study Assistant", version="2.0.0")

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(uploads_router)
app.include_router(admin_router)
app.include_router(chat_router)
app.include_router(share_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
