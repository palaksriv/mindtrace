"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the MindTrace API."""

    app_name: str = "MindTrace API"
    environment: str = "development"
    database_url: str = "sqlite:///./mindtrace.db"
    cors_origins: str = "http://localhost:5173"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=60, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MINDTRACE_",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Return the configured comma-separated CORS origins."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
