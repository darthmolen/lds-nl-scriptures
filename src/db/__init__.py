"""Database module for Scripture Search project.

Contains SQLAlchemy configuration and ORM models for:
- scriptures: verse-level scripture data with embeddings
- cfm_lessons: Come Follow Me lesson content
- conference_paragraphs: General Conference talk paragraphs with embeddings
"""

from src.db.config import get_session, engine, SessionLocal
from src.db.models import Base, Scripture, CFMLesson, ConferenceParagraph

__all__ = [
    "get_session",
    "engine",
    "SessionLocal",
    "Base",
    "Scripture",
    "CFMLesson",
    "ConferenceParagraph",
]
