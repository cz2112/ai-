from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.services.admin_bootstrap import ensure_default_admin
from tests.conftest import TestingSessionLocal


def test_default_admin_is_created_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_ENABLED", True)
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_USERNAME", "bootstrap_admin")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_EMAIL", "bootstrap@example.com")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_PASSWORD", "bootstrap-pass")

    db = TestingSessionLocal()
    try:
        result = ensure_default_admin(db)
        admin = db.query(User).filter(User.username == "bootstrap_admin").first()
        assert result == "created"
        assert admin is not None
        assert admin.is_admin is True
        assert admin.is_active is True
        assert admin.is_verified is True
        assert verify_password("bootstrap-pass", admin.hashed_password)
    finally:
        db.close()


def test_existing_user_is_promoted_to_admin(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_ENABLED", True)
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_USERNAME", "existing_admin")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_EMAIL", "existing@example.com")
    monkeypatch.setattr(settings, "DEFAULT_ADMIN_PASSWORD", "bootstrap-pass")

    db = TestingSessionLocal()
    try:
        user = User(
            username="existing_admin",
            email="existing@example.com",
            hashed_password="plain-text-password",
            is_admin=False,
            is_active=False,
            is_verified=False,
        )
        db.add(user)
        db.commit()

        result = ensure_default_admin(db)
        refreshed = db.query(User).filter(User.username == "existing_admin").first()

        assert result == "promoted"
        assert refreshed is not None
        assert refreshed.is_admin is True
        assert refreshed.is_active is True
        assert refreshed.is_verified is True
        assert refreshed.hashed_password == "plain-text-password"
    finally:
        db.close()
