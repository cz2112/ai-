import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.core.validators import validate_file_magic
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.upload import Upload
from app.models.tag import Tag
# from app.models.course import Course
# from app.models.study_material import Summary, KeyConcept, Flashcard
# from app.models.study_session import StudySession, FlashcardReview
# from app.models.share import SharedUpload
from app.schemas.upload import (
    UploadResponse, UploadDetailResponse, FlashcardUpdate, FlashcardResponse,
    CourseCreate, CourseResponse, StatsResponse, QuotaResponse,
    SummaryUpdate, SummaryResponse, KeyConceptUpdate, KeyConceptResponse,
    TagCreate, TagResponse, StudySessionCreate, StudySessionResponse,
    FlashcardReviewCreate, FlashcardReviewResponse, DueFlashcardResponse,
)

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {"pdf", "mp3", "wav", "pptx", "ppt", "docx", "png", "jpg", "jpeg"}


# ── Courses ──────────────────────────────────────────────

@router.get("/courses", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # courses = db.query(Course).filter(Course.user_id == current_user.id).order_by(Course.name).all()
    return []


@router.post("/courses", response_model=CourseResponse)
def create_course(data: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Courses disabled temporarily")


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Courses disabled temporarily")


# ── Stats & Quota ────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).all()
    by_status = defaultdict(int)
    by_date = defaultdict(int)
    for u in uploads:
        by_status[u.status] += 1
        date_key = u.created_at.strftime("%Y-%m-%d") if u.created_at else "unknown"
        by_date[date_key] += 1

    uploads_by_date = [{"date": k, "count": v} for k, v in sorted(by_date.items())]

    return StatsResponse(
        total_uploads=len(uploads),
        completed_uploads=by_status.get("Completed", 0),
        total_flashcards=0,
        known_flashcards=0,
        total_concepts=0,
        uploads_by_date=uploads_by_date,
        uploads_by_status=dict(by_status),
        study_activity_by_date=[],
    )


@router.get("/quota", response_model=QuotaResponse)
def get_quota(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    used = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    return QuotaResponse(
        uploads_used=used,
        uploads_limit=settings.MAX_UPLOADS_PER_USER,
        max_file_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_audio_minutes=settings.MAX_AUDIO_MINUTES,
        max_pdf_pages=settings.MAX_PDF_PAGES,
    )


# ── Upload CRUD ──────────────────────────────────────────

@router.post("/", response_model=UploadResponse)
@limiter.limit("10/minute")
def create_upload(
    request: Request,
    file: UploadFile = File(...),
    course_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    used = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    if used >= settings.MAX_UPLOADS_PER_USER:
        raise HTTPException(status_code=400, detail=f"Upload quota reached ({settings.MAX_UPLOADS_PER_USER})")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = file.file.read()
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")

    if not validate_file_magic(content, ext):
        raise HTTPException(status_code=400, detail="File content does not match its extension")

    with open(file_path, "wb") as f:
        f.write(content)

    upload = Upload(
        user_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        file_path=file_path,
        file_size=file_size,
        status="Pending",
        course_id=course_id,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)

    # from app.workers.tasks import process_upload
    # process_upload.delay(upload.id)

    return upload


@router.get("/", response_model=list[UploadResponse])
def list_uploads(
    search: str = Query(None),
    status: str = Query(None),
    course_id: int = Query(None),
    tag: str = Query(None),
    sort: str = Query("newest"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Upload).filter(Upload.user_id == current_user.id)
    if search:
        q = q.filter(Upload.filename.ilike(f"%{search}%"))
    if status:
        q = q.filter(Upload.status == status)
    if course_id is not None:
        q = q.filter(Upload.course_id == course_id)
    # if tag:
    #     q = q.join(Upload.tags).filter(Tag.name == tag)
    if sort == "oldest":
        q = q.order_by(Upload.created_at.asc())
    elif sort == "name":
        q = q.order_by(Upload.filename.asc())
    elif sort == "size":
        q = q.order_by(Upload.file_size.desc())
    else:
        q = q.order_by(Upload.created_at.desc())
    return q.all()


@router.get("/{upload_id}", response_model=UploadDetailResponse)
def get_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.delete("/{upload_id}")
def delete_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if os.path.exists(upload.file_path):
        os.remove(upload.file_path)
    db.delete(upload)
    db.commit()
    return {"detail": "Deleted"}


# ── Tags ─────────────────────────────────────────────────

@router.get("/tags/list", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tag).filter(Tag.user_id == current_user.id).order_by(Tag.name).all()


@router.post("/tags", response_model=TagResponse)
def create_tag(data: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Tag).filter(Tag.user_id == current_user.id, Tag.name == data.name).first()
    if existing:
        return existing
    tag = Tag(user_id=current_user.id, name=data.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"detail": "Deleted"}