"""Scripture Search API package.

FastAPI-based REST API for semantic search across scriptures,
Come Follow Me lessons, and General Conference talks.
"""

from src.api.main import app, create_app
from src.api.config import APISettings, get_settings

__all__ = [
    "app",
    "create_app",
    "APISettings",
    "get_settings",
]
