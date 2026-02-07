from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from app.core.sanitize import validate_username, validate_email


class UserCreate(BaseModel):
    username: str
    email: str
    password: str

    @field_validator('username')
    @classmethod
    def check_username(cls, v):
        return validate_username(v)

    @field_validator('email')
    @classmethod
    def check_email(cls, v):
        return validate_email(v)

    @field_validator('password')
    @classmethod
    def check_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Admin schemas ────────────────────────────────────────

class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime | None = None
    upload_count: int = 0

    class Config:
        from_attributes = True


class AdminUploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    is_shared: bool = False
    created_at: datetime | None = None
    username: str = ""

    class Config:
        from_attributes = True


class AdminStatsResponse(BaseModel):
    total_users: int
    total_uploads: int
    total_storage_mb: float
    uploads_by_status: dict[str, int]
    recent_users: list[AdminUserResponse]


class AdminSettingsUpdate(BaseModel):
    max_uploads_per_user: Optional[int] = None
    max_upload_size_mb: Optional[int] = None
    max_audio_minutes: Optional[int] = None
    max_pdf_pages: Optional[int] = None


class AdminSettingsResponse(BaseModel):
    max_uploads_per_user: int
    max_upload_size_mb: int
    max_audio_minutes: int
    max_pdf_pages: int
