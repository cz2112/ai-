from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.share import GroupMember, SharedUpload
from app.models.upload import Upload
from app.models.user import User


def get_user_group_ids(db: Session, user_id: int) -> list[int]:
    return [row.group_id for row in db.query(GroupMember).filter(GroupMember.user_id == user_id).all()]


def user_can_access_upload_record(db: Session, user_id: int, upload: Upload | None) -> bool:
    if not upload:
        return False
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_admin:
        return True
    if upload.user_id == user_id or bool(upload.is_shared):
        return True

    if db.query(SharedUpload).filter(
        SharedUpload.upload_id == upload.id,
        SharedUpload.shared_with == user_id,
    ).first():
        return True

    group_ids = get_user_group_ids(db, user_id)
    if group_ids and db.query(SharedUpload).filter(
        SharedUpload.upload_id == upload.id,
        SharedUpload.group_id.in_(group_ids),
    ).first():
        return True

    if db.query(SharedUpload).filter(
        SharedUpload.upload_id == upload.id,
        SharedUpload.shared_with == None,
        SharedUpload.group_id == None,
    ).first():
        return True

    return False


def user_can_access_upload(db: Session, user_id: int, upload_id: int) -> bool:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    return user_can_access_upload_record(db, user_id, upload)


def require_upload_read_access(db: Session, upload_id: int, user_id: int) -> Upload:
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not user_can_access_upload_record(db, user_id, upload):
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload
