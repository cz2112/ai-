from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from datetime import datetime, timezone
from app.core.database import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=True)
    activity_type = Column(String(50), nullable=False)  # "flashcard_review", "chat", "read_summary"
    cards_reviewed = Column(Integer, default=0)
    cards_known = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"

    id = Column(Integer, primary_key=True, index=True)
    flashcard_id = Column(Integer, ForeignKey("flashcards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quality = Column(Integer, nullable=False)  # 0-5 (SM-2 algorithm)
    easiness = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
