from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base
from app.models.tag import upload_tags


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, mp3, wav, pptx, docx, png, jpg
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(20), default="Pending")  # Pending/Processing/Completed/Failed
    is_shared = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="uploads")
    course = relationship("Course", back_populates="uploads")
    summary = relationship("Summary", back_populates="upload", uselist=False, cascade="all, delete-orphan")
    key_concepts = relationship("KeyConcept", back_populates="upload", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="upload", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="upload", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=upload_tags, back_populates="uploads")
