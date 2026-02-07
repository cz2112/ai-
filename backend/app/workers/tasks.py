from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.upload import Upload
from app.models.study_material import Summary, KeyConcept, Flashcard
from app.services.ai_service import (
    transcribe_audio, extract_pdf_text, extract_pptx_text,
    extract_docx_text, extract_image_text, detect_language,
    generate_summary, generate_key_concepts, generate_flashcards,
)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def process_upload(self, upload_id: int):
    db = SessionLocal()
    try:
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload:
            return

        upload.status = "Processing"
        db.commit()

        # Step 1: Extract text based on file type
        if upload.file_type in ("mp3", "wav"):
            text = transcribe_audio(upload.file_path)
        elif upload.file_type == "pdf":
            text = extract_pdf_text(upload.file_path)
        elif upload.file_type in ("pptx", "ppt"):
            text = extract_pptx_text(upload.file_path)
        elif upload.file_type == "docx":
            text = extract_docx_text(upload.file_path)
        elif upload.file_type in ("png", "jpg", "jpeg"):
            text = extract_image_text(upload.file_path)
        else:
            raise ValueError(f"Unsupported file type: {upload.file_type}")

        upload.transcript = text
        db.commit()

        # Step 1.5: Detect language
        lang = detect_language(text)
        upload.language = lang
        db.commit()

        # Step 2: Generate summary
        summary_text = generate_summary(text, lang=lang)
        db.add(Summary(upload_id=upload.id, content=summary_text))
        db.commit()

        # Step 3: Generate key concepts with citations
        concepts = generate_key_concepts(text, lang=lang)
        for c in concepts:
            db.add(KeyConcept(
                upload_id=upload.id,
                title=c["title"],
                description=c["description"],
                citation=c.get("citation"),
            ))
        db.commit()

        # Step 4: Generate flashcards
        cards = generate_flashcards(text, lang=lang)
        for card in cards:
            db.add(Flashcard(
                upload_id=upload.id,
                question=card["question"],
                answer=card["answer"],
            ))
        db.commit()

        upload.status = "Completed"
        db.commit()

    except Exception as exc:
        db.rollback()
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if upload:
            upload.status = "Failed"
            upload.error_message = str(exc)[:500]
            db.commit()
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
    finally:
        db.close()
