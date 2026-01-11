"""SQLAlchemy ORM models for Scripture Search project.

Models:
- Scripture: verse-level scripture data with vector embeddings
- CFMLesson: Come Follow Me lesson content with embeddings
"""

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Column,
    Integer,
    String,
    Text,
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Scripture(Base):
    """Scripture verse model.

    Stores individual scripture verses with metadata and optional embeddings.

    Attributes:
        id: Primary key
        volume: Scripture volume (oldtestament, newtestament, bookofmormon,
                doctrineandcovenants, pearlofgreatprice)
        book: Book name (genesis, 1nephi, mosiah, etc.)
        chapter: Chapter number
        verse: Verse number
        text: Full verse text
        lang: Language code ('en', 'es')
        footnotes: JSON object containing footnote references and content
        context_text: Concatenated text from +/-2 verses for embedding context
        embedding: Vector embedding (1536 dimensions for text-embedding-3-small)
        created_at: Timestamp of record creation
    """
    __tablename__ = "scriptures"

    id = Column(Integer, primary_key=True)
    volume = Column(String(50), nullable=False, index=True)
    book = Column(String(50), nullable=False, index=True)
    chapter = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    lang = Column(String(5), nullable=False, index=True)
    footnotes = Column(JSONB)
    context_text = Column(Text)  # NULL until Phase 3 embedding generation
    embedding = Column(Vector(1536))  # NULL until Phase 3 embedding generation
    created_at = Column(TIMESTAMP, server_default=sql_text("NOW()"))

    def __repr__(self) -> str:
        return (
            f"<Scripture(id={self.id}, {self.volume}/{self.book} "
            f"{self.chapter}:{self.verse}, lang={self.lang})>"
        )


class CFMLesson(Base):
    """Come Follow Me lesson model.

    Stores CFM lesson content with scripture references and embeddings.

    Attributes:
        id: Primary key
        year: Lesson year (e.g., 2024, 2025)
        testament: Scripture focus (ot, nt, bom, dc)
        lesson_id: Unique lesson identifier (e.g., "001-conversion")
        title: Lesson title
        date_range: Date range string for the lesson
        scripture_refs: Array of scripture reference strings
        content: Plain text content of the lesson
        lang: Language code ('en', 'es')
        embedding: Vector embedding (1536 dimensions)
        created_at: Timestamp of record creation
    """
    __tablename__ = "cfm_lessons"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, index=True)
    testament = Column(String(50), index=True)
    lesson_id = Column(String(100), nullable=False)
    title = Column(Text)
    date_range = Column(String(100))
    scripture_refs = Column(ARRAY(Text))
    content = Column(Text)
    lang = Column(String(5), nullable=False, index=True)
    embedding = Column(Vector(1536))  # NULL until Phase 3 embedding generation
    created_at = Column(TIMESTAMP, server_default=sql_text("NOW()"))

    def __repr__(self) -> str:
        return (
            f"<CFMLesson(id={self.id}, year={self.year}, "
            f"lesson_id={self.lesson_id}, lang={self.lang})>"
        )
