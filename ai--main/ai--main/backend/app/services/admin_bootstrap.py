import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


logger = logging.getLogger(__name__)


def _config_values() -> tuple[str, str, str]:
    return (
        (settings.DEFAULT_ADMIN_USERNAME or "").strip(),
        (settings.DEFAULT_ADMIN_EMAIL or "").strip().lower(),
        settings.DEFAULT_ADMIN_PASSWORD or "",
    )


def ensure_default_admin(db: Session) -> str:
    if not settings.DEFAULT_ADMIN_ENABLED:
        return "disabled"

    username, email, password = _config_values()
    if not username or not email or not password:
        logger.warning(
            "Default admin bootstrap is enabled, but username/email/password is incomplete. "
            "Set DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, and DEFAULT_ADMIN_PASSWORD."
        )
        return "invalid_config"

    if len(password) < 6:
        logger.warning("Default admin bootstrap password must be at least 6 characters.")
        return "invalid_config"

    user_by_username = db.query(User).filter(User.username == username).first()
    user_by_email = db.query(User).filter(User.email == email).first()

    if user_by_username and user_by_email and user_by_username.id != user_by_email.id:
        logger.warning(
            "Default admin bootstrap skipped because username '%s' and email '%s' belong to different users.",
            username,
            email,
        )
        return "conflict"

    existing = user_by_username or user_by_email
    if existing:
        changed = False
        if not existing.is_admin:
            existing.is_admin = True
            changed = True
        if not existing.is_active:
            existing.is_active = True
            changed = True
        if not existing.is_verified:
            existing.is_verified = True
            changed = True

        if changed:
            db.commit()
            logger.info("Promoted existing user '%s' to admin during startup bootstrap.", existing.username)
            return "promoted"

        logger.info("Default admin '%s' already exists.", existing.username)
        return "exists"

    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=True,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    logger.info("Created default admin '%s' during startup bootstrap.", username)
    return "created"


def bootstrap_default_admin() -> str:
    db = SessionLocal()
    try:
        return ensure_default_admin(db)
    except Exception:
        logger.exception("Default admin bootstrap failed.")
        return "error"
    finally:
        db.close()
