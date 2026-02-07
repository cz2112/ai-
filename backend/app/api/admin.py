import os
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_admin_user
from app.models.user import User
from app.models.upload import Upload
from app.schemas.user import (
    AdminUserResponse,
    AdminUploadResponse,
    AdminStatsResponse,
    AdminSettingsUpdate,
    AdminSettingsResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Users ────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserResponse])
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        count = db.query(Upload).filter(Upload.user_id == u.id).count()
        result.append(AdminUserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            is_admin=u.is_admin,
            is_active=u.is_active,
            created_at=u.created_at,
            upload_count=count,
        ))
    return result


@router.patch("/users/{user_id}/toggle")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot disable yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    # Delete user's upload files from disk
    uploads = db.query(Upload).filter(Upload.user_id == user_id).all()
    for u in uploads:
        if u.file_path and os.path.exists(u.file_path):
            os.remove(u.file_path)
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


# ── Uploads ──────────────────────────────────────────────

@router.get("/uploads", response_model=list[AdminUploadResponse])
def list_all_uploads(
    search: str = Query(None),
    status: str = Query(None),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    q = db.query(Upload).order_by(Upload.created_at.desc())
    if search:
        q = q.filter(Upload.filename.ilike(f"%{search}%"))
    if status:
        q = q.filter(Upload.status == status)
    if user_id is not None:
        q = q.filter(Upload.user_id == user_id)
    uploads = q.limit(200).all()
    result = []
    for u in uploads:
        owner = db.query(User).filter(User.id == u.user_id).first()
        result.append(AdminUploadResponse(
            id=u.id,
            filename=u.filename,
            file_type=u.file_type,
            file_size=u.file_size,
            status=u.status,
            is_shared=u.is_shared or False,
            created_at=u.created_at,
            username=owner.username if owner else "deleted",
        ))
    return result


@router.patch("/uploads/{upload_id}/toggle-share")
def toggle_upload_share(upload_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    upload.is_shared = not (upload.is_shared or False)
    db.commit()
    return {"id": upload.id, "is_shared": upload.is_shared}


@router.delete("/uploads/{upload_id}")
def delete_any_upload(upload_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.file_path and os.path.exists(upload.file_path):
        os.remove(upload.file_path)
    db.delete(upload)
    db.commit()
    return {"detail": "Upload deleted"}


# ── Stats ────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
def system_stats(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    total_users = db.query(User).count()
    total_uploads = db.query(Upload).count()
    total_bytes = db.query(func.coalesce(func.sum(Upload.file_size), 0)).scalar()
    total_storage_mb = round(total_bytes / (1024 * 1024), 2)

    by_status = defaultdict(int)
    for row in db.query(Upload.status, func.count()).group_by(Upload.status).all():
        by_status[row[0]] = row[1]

    recent = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_users = []
    for u in recent:
        count = db.query(Upload).filter(Upload.user_id == u.id).count()
        recent_users.append(AdminUserResponse(
            id=u.id, username=u.username, email=u.email,
            is_admin=u.is_admin, is_active=u.is_active,
            created_at=u.created_at, upload_count=count,
        ))

    return AdminStatsResponse(
        total_users=total_users,
        total_uploads=total_uploads,
        total_storage_mb=total_storage_mb,
        uploads_by_status=dict(by_status),
        recent_users=recent_users,
    )


# ── Settings ─────────────────────────────────────────────

@router.get("/settings", response_model=AdminSettingsResponse)
def get_settings(admin: User = Depends(get_admin_user)):
    return AdminSettingsResponse(
        max_uploads_per_user=settings.MAX_UPLOADS_PER_USER,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_audio_minutes=settings.MAX_AUDIO_MINUTES,
        max_pdf_pages=settings.MAX_PDF_PAGES,
    )


@router.patch("/settings", response_model=AdminSettingsResponse)
def update_settings(data: AdminSettingsUpdate, admin: User = Depends(get_admin_user)):
    if data.max_uploads_per_user is not None:
        settings.MAX_UPLOADS_PER_USER = data.max_uploads_per_user
    if data.max_upload_size_mb is not None:
        settings.MAX_UPLOAD_SIZE_MB = data.max_upload_size_mb
    if data.max_audio_minutes is not None:
        settings.MAX_AUDIO_MINUTES = data.max_audio_minutes
    if data.max_pdf_pages is not None:
        settings.MAX_PDF_PAGES = data.max_pdf_pages
    return AdminSettingsResponse(
        max_uploads_per_user=settings.MAX_UPLOADS_PER_USER,
        max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
        max_audio_minutes=settings.MAX_AUDIO_MINUTES,
        max_pdf_pages=settings.MAX_PDF_PAGES,
    )
