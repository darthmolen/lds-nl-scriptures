#!/usr/bin/env python3
"""Generate embeddings for conference paragraphs with ±2 paragraph context.

Follows the same context strategy as scripture embeddings: each paragraph
is embedded with surrounding context from the same talk.

Usage:
    # Generate for English:
    python -m src.embeddings.generate_conference --lang en

    # With custom batch size:
    python -m src.embeddings.generate_conference --lang en --batch-size 20

    # Limit for testing:
    python -m src.embeddings.generate_conference --lang en --limit 100
"""

import argparse
import time
from typing import Optional

from sqlalchemy import text

from src.db import get_session
from src.db.models import ConferenceParagraph
from src.embeddings.client import get_embeddings


def build_context(session, paragraph: ConferenceParagraph, context_window: int = 2) -> str:
    """Build embedding context for a paragraph.

    Includes ±context_window paragraphs from the same talk.

    Format:
    [Talk Title] by [Speaker Name]

    [Previous paragraphs...]
    [Current paragraph]
    [Following paragraphs...]

    Args:
        session: Database session
        paragraph: The paragraph to build context for
        context_window: Number of paragraphs before/after to include

    Returns:
        Context string for embedding
    """
    parts = []

    # Header with talk metadata
    header = paragraph.talk_title or "Conference Talk"
    if paragraph.speaker_name:
        header += f" by {paragraph.speaker_name}"
    parts.append(header)
    parts.append("")

    # Get surrounding paragraphs from same talk
    min_num = max(1, paragraph.paragraph_num - context_window)
    max_num = paragraph.paragraph_num + context_window

    result = session.execute(
        text("""
            SELECT paragraph_num, text
            FROM conference_paragraphs
            WHERE talk_uri = :uri AND lang = :lang
              AND paragraph_num >= :min_num AND paragraph_num <= :max_num
            ORDER BY paragraph_num
        """),
        {
            "uri": paragraph.talk_uri,
            "lang": paragraph.lang,
            "min_num": min_num,
            "max_num": max_num,
        },
    )

    for row in result.fetchall():
        if row.paragraph_num == paragraph.paragraph_num:
            # Mark current paragraph
            parts.append(f">>> {row.text}")
        else:
            parts.append(row.text)

    return "\n".join(parts)


def get_paragraphs_without_embeddings(
    session, lang: str, limit: Optional[int] = None
) -> list[ConferenceParagraph]:
    """Get conference paragraphs that don't have embeddings yet."""
    query = session.query(ConferenceParagraph).filter(
        ConferenceParagraph.lang == lang,
        ConferenceParagraph.embedding.is_(None),
    ).order_by(ConferenceParagraph.id)

    if limit:
        query = query.limit(limit)

    return query.all()


def process_batch(
    session,
    paragraphs: list[ConferenceParagraph],
    batch_num: int,
    total_batches: int,
) -> None:
    """Process a batch of paragraphs."""
    # Build context texts
    texts = []
    for para in paragraphs:
        context = build_context(session, para)
        texts.append(context)
        # Also store context_text for reference
        para.context_text = context

    # Get embeddings
    embeddings = get_embeddings(texts)

    # Update database
    for para, embedding in zip(paragraphs, embeddings):
        para.embedding = embedding

    session.commit()
    print(f"Batch {batch_num}/{total_batches}: Processed {len(paragraphs)} paragraphs")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for conference paragraphs"
    )
    parser.add_argument(
        "--lang",
        choices=["en", "es"],
        default="en",
        help="Language to process",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of paragraphs per batch",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between batches (seconds)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of paragraphs to process (for testing)",
    )
    args = parser.parse_args()

    print(f"Starting conference embedding generation for {args.lang}...")

    with get_session() as session:
        paragraphs = get_paragraphs_without_embeddings(session, args.lang, args.limit)
        total = len(paragraphs)

        if total == 0:
            print("No paragraphs without embeddings found.")
            return

        print(f"Found {total} paragraphs without embeddings")

        total_batches = (total + args.batch_size - 1) // args.batch_size

        for i in range(0, total, args.batch_size):
            batch = paragraphs[i:i + args.batch_size]
            batch_num = i // args.batch_size + 1

            process_batch(session, batch, batch_num, total_batches)

            if i + args.batch_size < total:
                time.sleep(args.delay)

    print(f"\nCompleted! Generated embeddings for {total} conference paragraphs.")


if __name__ == "__main__":
    main()
