from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    is_shared: bool = False
    error_message: Optional[str] = None
    course_id: Optional[int] = None
    course_name: Optional[str] = None
    language: str = "en"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True


class SummaryUpdate(BaseModel):
    content: str


class KeyConceptResponse(BaseModel):
    id: int
    title: str
    description: str
    citation: Optional[str] = None

    class Config:
        from_attributes = True


class KeyConceptUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class FlashcardResponse(BaseModel):
    id: int
    question: str
    answer: str
    is_known: bool

    class Config:
        from_attributes = True


class FlashcardUpdate(BaseModel):
    is_known: Optional[bool] = None
    question: Optional[str] = None
    answer: Optional[str] = None


class UploadDetailResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    is_shared: bool = False
    error_message: Optional[str] = None
    transcript: Optional[str] = None
    course_id: Optional[int] = None
    language: str = "en"
    summary: Optional[SummaryResponse] = None
    key_concepts: list[KeyConceptResponse] = Field(default_factory=list)
    flashcards: list[FlashcardResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    name: str


class CourseResponse(BaseModel):
    id: int
    name: str
    upload_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_uploads: int
    completed_uploads: int
    total_flashcards: int
    known_flashcards: int
    total_concepts: int
    uploads_by_date: list[dict]
    uploads_by_status: dict
    study_activity_by_date: list[dict] = []


class QuotaResponse(BaseModel):
    uploads_used: int
    uploads_limit: int
    max_file_size_mb: int
    max_audio_minutes: int
    max_pdf_pages: int


class ExportResponse(BaseModel):
    content: str
    filename: str


# ── Tag schemas ──────────────────────────────────────────

class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ── Study Session schemas ────────────────────────────────

class StudySessionCreate(BaseModel):
    upload_id: Optional[int] = None
    activity_type: str
    cards_reviewed: int = 0
    cards_known: int = 0
    duration_seconds: int = 0


class StudySessionResponse(BaseModel):
    id: int
    upload_id: Optional[int] = None
    activity_type: str
    cards_reviewed: int
    cards_known: int
    duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Flashcard Review (SM-2) schemas ──────────────────────

class FlashcardReviewCreate(BaseModel):
    quality: int  # 0-5


class FlashcardReviewResponse(BaseModel):
    flashcard_id: int
    next_review: datetime
    easiness: float
    interval_days: int
    repetitions: int

    class Config:
        from_attributes = True


class DueFlashcardResponse(BaseModel):
    id: int
    question: str
    answer: str
    upload_id: int
    filename: str = ""
    next_review: Optional[datetime] = None
    easiness: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
