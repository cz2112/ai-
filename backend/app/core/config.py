import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)


def _default_ai_provider() -> str:
    if os.getenv("AI_PROVIDER"):
        return os.getenv("AI_PROVIDER", "deepseek").lower()
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return "deepseek"


def _default_llm_model(provider: str) -> str:
    return "deepseek-v4-flash"


def _default_ai_base_url(provider: str) -> str:
    return "https://api.deepseek.com"


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://studyapp:studyapp123@localhost:5432/smart_study",
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "465"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.qq.com")

    AI_PROVIDER: str = _default_ai_provider()
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", _default_ai_base_url(_default_ai_provider()))
    LLM_MODEL: str = os.getenv("LLM_MODEL", _default_llm_model(_default_ai_provider()))
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")
    GLM_BASE_URL: str = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    GLM_ASR_MODEL: str = os.getenv("GLM_ASR_MODEL", "glm-asr-2512")
    GLM_VISION_MODEL: str = os.getenv("GLM_VISION_MODEL", "glm-4.6v")
    GLM_OCR_MODEL: str = os.getenv("GLM_OCR_MODEL", "glm-ocr")
    GLM_ASR_CHUNK_SECONDS: int = int(os.getenv("GLM_ASR_CHUNK_SECONDS", "25"))
    GLM_VIDEO_FRAME_COUNT: int = int(os.getenv("GLM_VIDEO_FRAME_COUNT", "6"))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DEFAULT_ADMIN_ENABLED: bool = _env_flag("DEFAULT_ADMIN_ENABLED", "false")
    DEFAULT_ADMIN_USERNAME: str = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "")

    MAX_UPLOADS_PER_USER: int = int(os.getenv("MAX_UPLOADS_PER_USER", "100"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    MAX_AUDIO_MINUTES: int = int(os.getenv("MAX_AUDIO_MINUTES", "120"))
    MAX_PDF_PAGES: int = int(os.getenv("MAX_PDF_PAGES", "500"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))

    class Config:
        extra = "ignore"


settings = Settings()
