"""API dependency injection module.

Provides FastAPI dependencies for database sessions and embedding clients.
Reuses existing components from src/db and src/embeddings.
"""

from typing import Generator

from openai import AzureOpenAI
from sqlalchemy.orm import Session

from src.db.config import SessionLocal
from src.embeddings.client import get_embedding_client as _get_embedding_client


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for FastAPI request lifecycle.

    This is a FastAPI dependency that yields a SQLAlchemy session.
    The session is automatically closed when the request completes.

    Yields:
        Session: SQLAlchemy session object.

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_embedding_client() -> AzureOpenAI:
    """Provide an Azure OpenAI client for embedding generation.

    This is a FastAPI dependency that returns the embedding client.
    The client is created fresh for each request.

    Returns:
        AzureOpenAI: Configured Azure OpenAI client.

    Example:
        @app.post("/search")
        def search(client: AzureOpenAI = Depends(get_embedding_client)):
            embeddings = client.embeddings.create(...)
    """
    return _get_embedding_client()
