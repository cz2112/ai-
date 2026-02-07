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
from app.models.course import Course
from app.models.study_material import Summary, KeyConcept, Flashcard
from app.models.tag import Tag
from app.models.study_session import StudySession, FlashcardReview
from app.models.share import SharedUpload
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
    courses = db.query(Course).filter(Course.user_id == current_user.id).order_by(Course.name).all()
    result = []
    for c in courses:
        count = db.query(Upload).filter(Upload.course_id == c.id).count()
        result.append(CourseResponse(id=c.id, name=c.name, upload_count=count, created_at=c.created_at))
    return result


@router.post("/courses", response_model=CourseResponse)
def create_course(data: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = Course(user_id=current_user.id, name=data.name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseResponse(id=course.id, name=course.name, upload_count=0, created_at=course.created_at)


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.query(Upload).filter(Upload.course_id == course_id).update({"course_id": None})
    db.delete(course)
    db.commit()
    return {"detail": "Deleted"}


# ── Stats & Quota ────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).all()
    upload_ids = [u.id for u in uploads]

    total_fc = db.query(Flashcard).filter(Flashcard.upload_id.in_(upload_ids)).count() if upload_ids else 0
    known_fc = db.query(Flashcard).filter(Flashcard.upload_id.in_(upload_ids), Flashcard.is_known == True).count() if upload_ids else 0
    total_kc = db.query(KeyConcept).filter(KeyConcept.upload_id.in_(upload_ids)).count() if upload_ids else 0

    by_status = defaultdict(int)
    by_date = defaultdict(int)
    for u in uploads:
        by_status[u.status] += 1
        date_key = u.created_at.strftime("%Y-%m-%d") if u.created_at else "unknown"
        by_date[date_key] += 1

    uploads_by_date = [{"date": k, "count": v} for k, v in sorted(by_date.items())]

    # Study activity by date
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    activity_by_date = defaultdict(int)
    for s in sessions:
        date_key = s.created_at.strftime("%Y-%m-%d") if s.created_at else "unknown"
        activity_by_date[date_key] += 1
    study_activity = [{"date": k, "count": v} for k, v in sorted(activity_by_date.items())]

    return StatsResponse(
        total_uploads=len(uploads),
        completed_uploads=by_status.get("Completed", 0),
        total_flashcards=total_fc,
        known_flashcards=known_fc,
        total_concepts=total_kc,
        uploads_by_date=uploads_by_date,
        uploads_by_status=dict(by_status),
        study_activity_by_date=study_activity,
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

    from app.workers.tasks import process_upload
    process_upload.delay(upload.id)

    return upload


@router.post("/batch", response_model=list[UploadResponse])
@limiter.limit("5/minute")
def batch_upload(
    request: Request,
    files: list[UploadFile] = File(...),
    course_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    used = db.query(Upload).filter(Upload.user_id == current_user.id).count()
    if used + len(files) > settings.MAX_UPLOADS_PER_USER:
        raise HTTPException(status_code=400, detail="Upload quota would be exceeded")

    results = []
    for file in files:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            continue

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

        content = file.file.read()
        file_size = len(content)
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            continue

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

        from app.workers.tasks import process_upload
        process_upload.delay(upload.id)
        results.append(upload)

    return results


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
    if tag:
        q = q.join(Upload.tags).filter(Tag.name == tag)
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
    # Owner can always access
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if upload:
        return upload
    # Check if shared with user or publicly shared
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    shared = db.query(SharedUpload).filter(
        SharedUpload.upload_id == upload_id,
        (SharedUpload.shared_with == current_user.id) | (SharedUpload.shared_with == None)
    ).first()
    if shared or upload.is_shared:
        return upload
    raise HTTPException(status_code=404, detail="Upload not found")


@router.patch("/{upload_id}", response_model=UploadResponse)
def update_upload(upload_id: int, course_id: int = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    upload.course_id = course_id
    db.commit()
    db.refresh(upload)
    return upload


@router.post("/{upload_id}/retry", response_model=UploadResponse)
def retry_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.status != "Failed":
        raise HTTPException(status_code=400, detail="Only failed uploads can be retried")
    upload.status = "Pending"
    upload.error_message = None
    db.commit()
    db.refresh(upload)
    from app.workers.tasks import process_upload
    process_upload.delay(upload.id)
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


# ── Export ────────────────────────────────────────────────

@router.get("/{upload_id}/export")
def export_upload(upload_id: int, fmt: str = Query("markdown"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.status != "Completed":
        raise HTTPException(status_code=400, detail="Upload not completed yet")

    lines = [f"# {upload.filename}\n"]

    if upload.summary:
        lines.append("## Summary\n")
        lines.append(upload.summary.content + "\n")

    if upload.key_concepts:
        lines.append("\n## Key Concepts\n")
        for kc in upload.key_concepts:
            lines.append(f"### {kc.title}\n")
            lines.append(f"{kc.description}\n")
            if kc.citation:
                lines.append(f"> {kc.citation}\n")

    if upload.flashcards:
        lines.append("\n## Flashcards\n")
        for i, fc in enumerate(upload.flashcards, 1):
            lines.append(f"**Q{i}:** {fc.question}\n")
            lines.append(f"**A{i}:** {fc.answer}\n")

    content = "\n".join(lines)
    safe_filename = upload.filename.rsplit(".", 1)[0] + "_study_notes.md"
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
        media_type="text/markdown",
    )


# ── Edit AI-generated content ────────────────────────────

@router.patch("/summary/{summary_id}", response_model=SummaryResponse)
def update_summary(summary_id: int, data: SummaryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = db.query(Summary).join(Upload).filter(Summary.id == summary_id, Upload.user_id == current_user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Summary not found")
    s.content = data.content
    db.commit()
    db.refresh(s)
    return s


@router.patch("/concepts/{concept_id}", response_model=KeyConceptResponse)
def update_concept(concept_id: int, data: KeyConceptUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    kc = db.query(KeyConcept).join(Upload).filter(KeyConcept.id == concept_id, Upload.user_id == current_user.id).first()
    if not kc:
        raise HTTPException(status_code=404, detail="Concept not found")
    if data.title is not None:
        kc.title = data.title
    if data.description is not None:
        kc.description = data.description
    db.commit()
    db.refresh(kc)
    return kc


@router.patch("/flashcards/{flashcard_id}", response_model=FlashcardResponse)
def update_flashcard(flashcard_id: int, data: FlashcardUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fc = db.query(Flashcard).join(Upload).filter(Flashcard.id == flashcard_id, Upload.user_id == current_user.id).first()
    if not fc:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    if data.is_known is not None:
        fc.is_known = data.is_known
    if data.question is not None:
        fc.question = data.question
    if data.answer is not None:
        fc.answer = data.answer
    db.commit()
    db.refresh(fc)
    return fc


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


@router.post("/{upload_id}/tags/{tag_id}")
def add_tag_to_upload(upload_id: int, tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag not in upload.tags:
        upload.tags.append(tag)
        db.commit()
    return {"detail": "Tag added"}


@router.delete("/{upload_id}/tags/{tag_id}")
def remove_tag_from_upload(upload_id: int, tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == current_user.id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag in upload.tags:
        upload.tags.remove(tag)
        db.commit()
    return {"detail": "Tag removed"}


# ── Knowledge Graph ──────────────────────────────────────

@router.get("/{upload_id}/knowledge-graph")
def get_knowledge_graph(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if not upload.transcript:
        raise HTTPException(status_code=400, detail="No transcript available")
    from app.services.ai_service import generate_knowledge_graph
    graph = generate_knowledge_graph(upload.transcript, lang=upload.language or "en")
    return graph


# ── Learning Path ────────────────────────────────────────

@router.get("/learning-path/recommend")
def get_learning_path(upload_id: int = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if upload_id:
        uploads = db.query(Upload).filter(
            Upload.id == upload_id, Upload.user_id == current_user.id, Upload.status == "Completed"
        ).all()
    else:
        uploads = db.query(Upload).filter(
            Upload.user_id == current_user.id, Upload.status == "Completed"
        ).all()
    if not uploads:
        return []

    summaries = []
    for u in uploads:
        if u.summary:
            summaries.append(u.summary.content)

    upload_ids = [u.id for u in uploads]
    known_cards = db.query(Flashcard).filter(
        Flashcard.upload_id.in_(upload_ids), Flashcard.is_known == True
    ).all()
    known_concepts = [f"{fc.question}" for fc in known_cards[:30]]

    from app.services.ai_service import generate_learning_path
    path = generate_learning_path(summaries, known_concepts, lang=uploads[0].language or "en")
    return path


# ── Study Sessions ───────────────────────────────────────

@router.post("/study-sessions", response_model=StudySessionResponse)
def record_study_session(data: StudySessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = StudySession(
        user_id=current_user.id,
        upload_id=data.upload_id,
        activity_type=data.activity_type,
        cards_reviewed=data.cards_reviewed,
        cards_known=data.cards_known,
        duration_seconds=data.duration_seconds,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/study-sessions/progress")
def get_study_progress(days: int = Query(30), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()
    by_date = defaultdict(lambda: {"cards_reviewed": 0, "cards_known": 0, "duration_minutes": 0, "sessions": 0})
    for s in sessions:
        date_key = s.created_at.strftime("%Y-%m-%d") if s.created_at else "unknown"
        by_date[date_key]["cards_reviewed"] += s.cards_reviewed
        by_date[date_key]["cards_known"] += s.cards_known
        by_date[date_key]["duration_minutes"] += s.duration_seconds // 60
        by_date[date_key]["sessions"] += 1

    result = [{"date": k, **v} for k, v in sorted(by_date.items())]
    return result[-days:]


# ── Spaced Repetition (SM-2) ────────────────────────────

@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardReviewResponse)
def review_flashcard(flashcard_id: int, data: FlashcardReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fc = db.query(Flashcard).join(Upload).filter(Flashcard.id == flashcard_id, Upload.user_id == current_user.id).first()
    if not fc:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    if data.quality < 0 or data.quality > 5:
        raise HTTPException(status_code=400, detail="Quality must be 0-5")

    # Get last review or use defaults
    last_review = db.query(FlashcardReview).filter(
        FlashcardReview.flashcard_id == flashcard_id,
        FlashcardReview.user_id == current_user.id,
    ).order_by(FlashcardReview.reviewed_at.desc()).first()

    if last_review:
        reps = last_review.repetitions
        ease = last_review.easiness
        interval = last_review.interval_days
    else:
        reps, ease, interval = 0, 2.5, 0

    from app.services.spaced_repetition import sm2_algorithm
    new_reps, new_ease, new_interval, next_review = sm2_algorithm(data.quality, reps, ease, interval)

    review = FlashcardReview(
        flashcard_id=flashcard_id,
        user_id=current_user.id,
        quality=data.quality,
        easiness=new_ease,
        interval_days=new_interval,
        repetitions=new_reps,
        next_review=next_review,
    )
    db.add(review)

    # Update flashcard known status
    fc.is_known = data.quality >= 3
    db.commit()
    db.refresh(review)

    return FlashcardReviewResponse(
        flashcard_id=flashcard_id,
        next_review=next_review,
        easiness=new_ease,
        interval_days=new_interval,
        repetitions=new_reps,
    )


@router.get("/flashcards/due", response_model=list[DueFlashcardResponse])
def get_due_flashcards(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id, Upload.status == "Completed").all()
    upload_ids = [u.id for u in uploads]
    upload_map = {u.id: u.filename for u in uploads}

    if not upload_ids:
        return []

    flashcards = db.query(Flashcard).filter(Flashcard.upload_id.in_(upload_ids)).all()
    now = datetime.now(timezone.utc)
    due = []

    for fc in flashcards:
        last_review = db.query(FlashcardReview).filter(
            FlashcardReview.flashcard_id == fc.id,
            FlashcardReview.user_id == current_user.id,
        ).order_by(FlashcardReview.reviewed_at.desc()).first()

        if last_review is None or last_review.next_review <= now:
            due.append(DueFlashcardResponse(
                id=fc.id,
                question=fc.question,
                answer=fc.answer,
                upload_id=fc.upload_id,
                filename=upload_map.get(fc.upload_id, ""),
                next_review=last_review.next_review if last_review else None,
                easiness=last_review.easiness if last_review else 2.5,
                interval_days=last_review.interval_days if last_review else 0,
                repetitions=last_review.repetitions if last_review else 0,
            ))

    return due
