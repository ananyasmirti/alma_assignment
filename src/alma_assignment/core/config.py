from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://alma:alma@localhost:5432/alma"

    # Auth
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "noreply@alma.com"
    attorney_email: str = "attorney@alma.com"

    # Storage
    storage_backend: str = "local"  # "local" or "s3"
    uploads_dir: str = "./uploads"

    # S3 (used when storage_backend = "s3")
    aws_bucket: str = ""
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
