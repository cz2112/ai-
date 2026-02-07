from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://studyapp:studyapp123@localhost:5432/smart_study"
    REDIS_URL: str = "redis://localhost:6379/0"
    GROQ_API_KEY: str = ""
    SECRET_KEY: str = "change-this-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    MAX_UPLOADS_PER_USER: int = 50
    MAX_AUDIO_MINUTES: int = 60
    MAX_PDF_PAGES: int = 200

    class Config:
        env_file = ".env"


settings = Settings()
