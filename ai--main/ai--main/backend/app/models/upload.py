from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(20), default="Pending")
    is_shared = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="uploads")
    course = relationship("Course", back_populates="uploads")
    summary = relationship("Summary", back_populates="upload", uselist=False, cascade="all, delete-orphan")
    key_concepts = relationship("KeyConcept", back_populates="upload", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="upload", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="upload", cascade="all, delete-orphan")

    @property
    def course_name(self):
        return self.course.name if self.course else None
