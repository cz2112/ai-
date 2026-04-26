import os
import uuid
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.validators import validate_file_magic
from app.models.course import Course
from app.models.study_session import FlashcardReview, StudySession
from app.models.study_material import Flashcard, KeyConcept, Summary
from app.models.tag import Tag
from app.models.upload import Upload
from app.models.user import User
from app.schemas.upload import (
    CourseCreate,
    CourseResponse,
    FlashcardResponse,
    FlashcardReviewCreate,
    FlashcardReviewResponse,
    FlashcardUpdate,
    KeyConceptResponse,
    KeyConceptUpdate,
    QuotaResponse,
    StatsResponse,
    SummaryResponse,
    SummaryUpdate,
    TagCreate,
    TagResponse,
    UploadDetailResponse,
    UploadResponse,
)
from app.services.ai_service import generate_knowledge_graph, generate_learning_path
from app.services.spaced_repetition import sm2_algorithm
from app.services.upload_access import require_upload_read_access
from app.workers import tasks as worker_tasks


router = APIRouter(prefix="/api/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {"pdf", "mp3", "wav", "mp4", "mov", "pptx", "ppt", "docx", "png", "jpg", "jpeg"}


def _require_owned_course(db: Session, course_id: int | None, user_id: int) -> Course | None:
    if course_id is None:
        return None
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == user_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _require_owned_upload(db: Session, upload_id: int, user_id: int) -> Upload:
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


def _ensure_quota(db: Session, user_id: int, incoming_count: int = 1) -> None:
    used = db.query(Upload).filter(Upload.user_id == user_id).count()
    if used + incoming_count > settings.MAX_UPLOADS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Upload quota reached ({settings.MAX_UPLOADS_PER_USER})",
        )


def _store_upload_file(file: UploadFile, course_id: int | None, db: Session, current_user: User) -> Upload:
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    _require_owned_course(db, course_id, current_user.id)

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")

    if not validate_file_magic(content, ext):
        raise HTTPException(status_code=400, detail="File content does not match its extension")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = upload_dir / safe_name
    file_path.write_bytes(content)

    upload = Upload(
        user_id=current_user.id,
        filename=file.filename,
        file_type=ext,
        file_path=str(file_path),
        file_size=len(content),
        status="Pending",
        course_id=course_id,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def _enqueue_upload_processing(background_tasks: BackgroundTasks, upload_id: int) -> None:
    try:
        worker_tasks.process_upload.delay(upload_id)
    except Exception:
        background_tasks.add_task(worker_tasks.process_upload.run, upload_id)


def _serialize_learning_path(steps: list[dict]) -> dict:
    serialized_steps = []
    for index, step in enumerate(steps, start=1):
        serialized_steps.append(
            {
                "step": step.get("step", index),
                "title": step.get("title") or step.get("topic") or f"Step {index}",
                "description": step.get("description") or step.get("reason") or "",
                "resources": step.get("resources") or "",
            }
        )
    return {"steps": serialized_steps}


@router.get("/courses", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Course)
        .filter(Course.user_id == current_user.id)
        .order_by(Course.name.asc(), Course.created_at.asc())
        .all()
    )


@router.post("/courses", response_model=CourseResponse)
def create_course(data: CourseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Course name cannot be empty")

    existing = db.query(Course).filter(Course.user_id == current_user.id, Course.name == name).first()
    if existing:
        return existing

    course = Course(user_id=current_user.id, name=name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/courses/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    course = db.query(Course).filter(Course.id == course_id, Course.user_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    db.query(Upload).filter(Upload.course_id == course.id, Upload.user_id == current_user.id).update(
        {Upload.course_id: None}
    )
    db.delete(course)
    db.commit()
    return {"detail": "Course deleted"}


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).all()
    upload_ids = [upload.id for upload in uploads]

    flashcards = db.query(Flashcard).filter(Flashcard.upload_id.in_(upload_ids)).all() if upload_ids else []
    concepts = db.query(KeyConcept).filter(KeyConcept.upload_id.in_(upload_ids)).all() if upload_ids else []

    uploads_by_status = defaultdict(int)
    uploads_by_date = defaultdict(int)
    study_activity = defaultdict(int)

    for upload in uploads:
        uploads_by_status[upload.status] += 1
        if upload.created_at:
            uploads_by_date[upload.created_at.strftime("%Y-%m-%d")] += 1

    review_rows = db.query(FlashcardReview).filter(FlashcardReview.user_id == current_user.id).all()
    session_rows = db.query(StudySession).filter(StudySession.user_id == current_user.id).all()

    for review in review_rows:
        if review.created_at:
            study_activity[review.created_at.strftime("%Y-%m-%d")] += 1

    for session in session_rows:
        if session.created_at:
            study_activity[session.created_at.strftime("%Y-%m-%d")] += 1

    return StatsResponse(
        total_uploads=len(uploads),
        completed_uploads=sum(1 for upload in uploads if upload.status == "Completed"),
        total_flashcards=len(flashcards),
        known_flashcards=sum(1 for flashcard in flashcards if flashcard.is_known),
        total_concepts=len(concepts),
        uploads_by_date=[{"date": key, "count": value} for key, value in sorted(uploads_by_date.items())],
        uploads_by_status=dict(uploads_by_status),
        study_activity_by_date=[{"date": key, "count": value} for key, value in sorted(study_activity.items())],
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


@router.post("/batch", response_model=list[UploadResponse])
@limiter.limit("5/minute")
def create_batch_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    course_id: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    _ensure_quota(db, current_user.id, len(files))
    uploads = []
    for file in files:
        upload = _store_upload_file(file, course_id, db, current_user)
        _enqueue_upload_processing(background_tasks, upload.id)
        uploads.append(upload)
    return uploads


@router.get("/tags/list", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tag).filter(Tag.user_id == current_user.id).order_by(Tag.name.asc()).all()


@router.post("/tags", response_model=TagResponse)
def create_tag(data: TagCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    existing = db.query(Tag).filter(Tag.user_id == current_user.id, Tag.name == name).first()
    if existing:
        return existing

    tag = Tag(user_id=current_user.id, name=name)
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


@router.patch("/summary/{summary_id}", response_model=SummaryResponse)
def update_summary(summary_id: int, data: SummaryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    summary = (
        db.query(Summary)
        .join(Upload, Summary.upload_id == Upload.id)
        .filter(Summary.id == summary_id, Upload.user_id == current_user.id)
        .first()
    )
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    summary.content = data.content.strip()
    db.commit()
    db.refresh(summary)
    return summary


@router.patch("/concepts/{concept_id}", response_model=KeyConceptResponse)
def update_concept(
    concept_id: int,
    data: KeyConceptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    concept = (
        db.query(KeyConcept)
        .join(Upload, KeyConcept.upload_id == Upload.id)
        .filter(KeyConcept.id == concept_id, Upload.user_id == current_user.id)
        .first()
    )
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    if data.title is not None:
        concept.title = data.title.strip()
    if data.description is not None:
        concept.description = data.description.strip()

    db.commit()
    db.refresh(concept)
    return concept


@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardReviewResponse)
def review_flashcard(
    flashcard_id: int,
    data: FlashcardReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not 0 <= data.quality <= 5:
        raise HTTPException(status_code=400, detail="Quality must be between 0 and 5")

    flashcard = (
        db.query(Flashcard)
        .join(Upload, Flashcard.upload_id == Upload.id)
        .filter(Flashcard.id == flashcard_id, Upload.user_id == current_user.id)
        .first()
    )
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    last_review = (
        db.query(FlashcardReview)
        .filter(FlashcardReview.flashcard_id == flashcard_id, FlashcardReview.user_id == current_user.id)
        .order_by(FlashcardReview.created_at.desc(), FlashcardReview.id.desc())
        .first()
    )

    repetitions, easiness, interval_days, next_review = sm2_algorithm(
        quality=data.quality,
        repetitions=last_review.repetitions if last_review else 0,
        easiness=last_review.easiness if last_review else 2.5,
        interval=last_review.interval_days if last_review else 0,
    )

    review = FlashcardReview(
        flashcard_id=flashcard_id,
        user_id=current_user.id,
        upload_id=flashcard.upload_id,
        quality=data.quality,
        easiness=easiness,
        interval_days=interval_days,
        repetitions=repetitions,
        next_review=next_review,
    )
    db.add(review)

    if data.quality >= 4:
        flashcard.is_known = True
    elif data.quality <= 1:
        flashcard.is_known = False

    db.add(
        StudySession(
            user_id=current_user.id,
            upload_id=flashcard.upload_id,
            activity_type="flashcard_review",
            cards_reviewed=1,
            cards_known=1 if flashcard.is_known else 0,
            duration_seconds=0,
        )
    )

    db.commit()
    db.refresh(review)
    return FlashcardReviewResponse(
        flashcard_id=flashcard.id,
        next_review=review.next_review,
        easiness=review.easiness,
        interval_days=review.interval_days,
        repetitions=review.repetitions,
    )


@router.patch("/flashcards/{flashcard_id}", response_model=FlashcardResponse)
def update_flashcard(
    flashcard_id: int,
    data: FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    flashcard = (
        db.query(Flashcard)
        .join(Upload, Flashcard.upload_id == Upload.id)
        .filter(Flashcard.id == flashcard_id, Upload.user_id == current_user.id)
        .first()
    )
    if not flashcard:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    if data.question is not None:
        flashcard.question = data.question.strip()
    if data.answer is not None:
        flashcard.answer = data.answer.strip()
    if data.is_known is not None:
        flashcard.is_known = data.is_known

    db.commit()
    db.refresh(flashcard)
    return flashcard


@router.get("/learning-path/recommend")
def recommend_learning_path(
    upload_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploads_query = db.query(Upload).filter(Upload.user_id == current_user.id, Upload.status == "Completed")
    if upload_id is not None:
        uploads_query = uploads_query.filter(Upload.id == upload_id)

    uploads = uploads_query.order_by(Upload.created_at.desc()).limit(5).all()
    if not uploads:
        raise HTTPException(status_code=404, detail="No completed uploads found")

    summaries = []
    known_concepts = []
    lang = "en"

    for upload in uploads:
        if upload.summary and upload.summary.content:
            summaries.append(upload.summary.content)
        elif upload.transcript:
            summaries.append(upload.transcript[:4000])
        known_concepts.extend([concept.title for concept in upload.key_concepts])
        if upload.language:
            lang = upload.language

    steps = generate_learning_path(summaries=summaries, known_concepts=known_concepts, lang=lang)
    return _serialize_learning_path(steps)


@router.post("/", response_model=UploadResponse)
@limiter.limit("10/minute")
def create_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    course_id: int | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_quota(db, current_user.id)
    upload = _store_upload_file(file, course_id, db, current_user)
    _enqueue_upload_processing(background_tasks, upload.id)
    return upload


@router.get("/", response_model=list[UploadResponse])
def list_uploads(
    search: str | None = Query(None),
    status: str | None = Query(None),
    course_id: int | None = Query(None),
    tag: str | None = Query(None),
    sort: str = Query("-created_at"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Upload).filter(Upload.user_id == current_user.id)

    if search:
        query = query.filter(Upload.filename.ilike(f"%{search}%"))
    if status:
        query = query.filter(Upload.status == status)
    if course_id is not None:
        query = query.filter(Upload.course_id == course_id)
    if tag:
        query = query.join(Tag, Tag.user_id == Upload.user_id).filter(Tag.name == tag)

    if sort in {"created_at", "oldest"}:
        query = query.order_by(Upload.created_at.asc(), Upload.id.asc())
    elif sort in {"filename", "name"}:
        query = query.order_by(Upload.filename.asc(), Upload.id.desc())
    elif sort in {"-filename", "name_desc"}:
        query = query.order_by(Upload.filename.desc(), Upload.id.desc())
    elif sort in {"size", "-file_size"}:
        query = query.order_by(Upload.file_size.desc(), Upload.id.desc())
    else:
        query = query.order_by(Upload.created_at.desc(), Upload.id.desc())

    return query.all()


@router.post("/{upload_id}/retry", response_model=UploadResponse)
def retry_upload(
    upload_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = _require_owned_upload(db, upload_id, current_user.id)
    upload.status = "Pending"
    upload.error_message = None
    db.commit()
    db.refresh(upload)
    _enqueue_upload_processing(background_tasks, upload.id)
    return upload


@router.get("/{upload_id}/knowledge-graph")
def get_knowledge_graph(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = require_upload_read_access(db, upload_id, current_user.id)
    text = upload.transcript or (upload.summary.content if upload.summary else "")
    if not text:
        raise HTTPException(status_code=400, detail="Upload has no content available")
    return generate_knowledge_graph(text, lang=upload.language or "en")


@router.get("/{upload_id}/export")
def export_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = require_upload_read_access(db, upload_id, current_user.id)

    lines = [f"# {upload.filename}", ""]

    if upload.summary and upload.summary.content:
        lines.extend(["## Summary", "", upload.summary.content, ""])

    if upload.key_concepts:
        lines.extend(["## Key Concepts", ""])
        for concept in upload.key_concepts:
            lines.append(f"- **{concept.title}**: {concept.description}")
            if concept.citation:
                lines.append(f"  - Citation: {concept.citation}")
        lines.append("")

    if upload.flashcards:
        lines.extend(["## Flashcards", ""])
        for index, flashcard in enumerate(upload.flashcards, start=1):
            lines.append(f"{index}. Q: {flashcard.question}")
            lines.append(f"   A: {flashcard.answer}")
        lines.append("")

    if upload.transcript:
        lines.extend(["## Transcript", "", upload.transcript])

    filename = f"{Path(upload.filename).stem}.md"
    return PlainTextResponse(
        "\n".join(lines).strip() + "\n",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{upload_id}", response_model=UploadDetailResponse)
def get_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return require_upload_read_access(db, upload_id, current_user.id)


@router.delete("/{upload_id}")
def delete_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    upload = _require_owned_upload(db, upload_id, current_user.id)
    if upload.file_path and os.path.exists(upload.file_path):
        os.remove(upload.file_path)
    db.delete(upload)
    db.commit()
    return {"detail": "Deleted"}
