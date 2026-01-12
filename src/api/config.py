"""API configuration module.

Provides Pydantic settings for the FastAPI application.
Loads configuration from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API configuration settings.

    All settings can be overridden via environment variables.
    Environment variables should be prefixed with the field name in uppercase.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = "Scripture Search API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings (comma-separated origins)
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Database (reused from existing config)
    database_url_sync: str = ""

    # Azure OpenAI settings
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> APISettings:
    """Get cached API settings instance.

    Returns:
        APISettings: Cached settings instance loaded from environment.
    """
    return APISettings()
