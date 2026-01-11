#!/usr/bin/env python3
"""Generate embeddings for scripture verses."""
import argparse
import time
from typing import Optional

from sqlalchemy import text as sql_text

from src.db import get_session
from src.db.models import Scripture
from src.embeddings.client import get_embeddings
from src.embeddings.context import build_context_for_verse


def get_verses_without_embeddings(session, lang: str, limit: Optional[int] = None):
    """Get verses that don't have embeddings yet."""
    query = session.query(Scripture).filter(
        Scripture.lang == lang,
        Scripture.embedding.is_(None)
    ).order_by(Scripture.id)

    if limit:
        query = query.limit(limit)

    return query.all()


def process_batch(session, verses: list[Scripture], batch_num: int, total_batches: int):
    """Process a batch of verses: build context and get embeddings."""
    # Build context texts
    context_texts = []
    for verse in verses:
        if verse.context_text:
            context_texts.append(verse.context_text)
        else:
            context = build_context_for_verse(session, verse)
            verse.context_text = context
            context_texts.append(context)

    # Get embeddings from Azure OpenAI
    embeddings = get_embeddings(context_texts)

    # Update verses with embeddings
    for verse, embedding in zip(verses, embeddings):
        verse.embedding = embedding

    session.commit()
    print(f"Batch {batch_num}/{total_batches}: Processed {len(verses)} verses")


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for scriptures")
    parser.add_argument("--lang", choices=["en", "es"], required=True,
                        help="Language to process")
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Batch size for API calls (default: 100)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between batches in seconds (default: 1.0)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of verses to process (for testing)")
    args = parser.parse_args()

    print(f"Starting embedding generation for {args.lang}...")

    with get_session() as session:
        # Get verses without embeddings
        verses = get_verses_without_embeddings(session, args.lang, args.limit)
        total = len(verses)

        if total == 0:
            print("No verses need embeddings. All done!")
            return

        print(f"Found {total} verses without embeddings")

        # Process in batches
        total_batches = (total + args.batch_size - 1) // args.batch_size

        for i in range(0, total, args.batch_size):
            batch = verses[i:i + args.batch_size]
            batch_num = (i // args.batch_size) + 1

            process_batch(session, batch, batch_num, total_batches)

            # Rate limit delay (skip on last batch)
            if i + args.batch_size < total:
                time.sleep(args.delay)

        print(f"\nCompleted! Generated embeddings for {total} verses.")


if __name__ == "__main__":
    main()
