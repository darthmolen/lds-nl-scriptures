#!/usr/bin/env python3
"""Generate embeddings for CFM lessons with referenced scripture context."""
import argparse
import re
import time
from typing import Optional

from src.db import get_session
from src.db.models import CFMLesson, Scripture
from src.embeddings.client import get_embeddings


def parse_scripture_ref(ref: str) -> Optional[tuple[str, int, int]]:
    """Parse a scripture reference like '2 Corinthians 5:17' or 'John 1:1-5'.

    Returns (book, chapter, verse_start) or None if unparseable.
    """
    # Clean up non-breaking spaces
    ref = ref.replace('\xa0', ' ').strip()

    # Pattern: optional number + book name + chapter:verse(-verse)
    pattern = r'^(\d?\s*\w+(?:\s+\w+)?)\s+(\d+):(\d+)(?:-\d+)?$'
    match = re.match(pattern, ref, re.IGNORECASE)

    if not match:
        return None

    book_name = match.group(1).strip().lower()
    chapter = int(match.group(2))
    verse = int(match.group(3))

    # Normalize book name to match our database format
    book_mapping = {
        '1 nephi': '1nephi', '2 nephi': '2nephi', '3 nephi': '3nephi', '4 nephi': '4nephi',
        '1 corinthians': '1corinthians', '2 corinthians': '2corinthians',
        '1 thessalonians': '1thessalonians', '2 thessalonians': '2thessalonians',
        '1 timothy': '1timothy', '2 timothy': '2timothy',
        '1 peter': '1peter', '2 peter': '2peter',
        '1 john': '1john', '2 john': '2john', '3 john': '3john',
        '1 samuel': '1samuel', '2 samuel': '2samuel',
        '1 kings': '1kings', '2 kings': '2kings',
        '1 chronicles': '1chronicles', '2 chronicles': '2chronicles',
        'song of solomon': 'songofsolomon',
        'doctrine and covenants': 'dc', 'd&c': 'dc',
    }

    book_id = book_mapping.get(book_name, book_name.replace(' ', ''))

    return (book_id, chapter, verse)


def lookup_verse_text(session, book: str, chapter: int, verse: int, lang: str) -> Optional[str]:
    """Look up a verse's text from the database."""
    result = session.query(Scripture.text).filter(
        Scripture.book == book,
        Scripture.chapter == chapter,
        Scripture.verse == verse,
        Scripture.lang == lang
    ).first()

    return result.text if result else None


def build_cfm_context(session, lesson: CFMLesson) -> str:
    """Build embedding context for a CFM lesson.

    Format:
    [Title] - Week [lesson_id], [date_range]
    Scripture References: [refs]

    [Referenced verse texts]

    [CFM commentary]
    """
    parts = []

    # Title and metadata
    header = f"{lesson.title}"
    if lesson.date_range:
        header += f" ({lesson.date_range})"
    parts.append(header)

    # Scripture references
    if lesson.scripture_refs:
        refs_str = ", ".join(lesson.scripture_refs)
        parts.append(f"Scripture References: {refs_str}")

        # Look up actual verse texts
        verse_texts = []
        for ref in lesson.scripture_refs[:10]:  # Limit to first 10 refs
            parsed = parse_scripture_ref(ref)
            if parsed:
                book, chapter, verse = parsed
                text = lookup_verse_text(session, book, chapter, verse, lesson.lang)
                if text:
                    verse_texts.append(f"{ref}: {text}")

        if verse_texts:
            parts.append("\nReferenced Scriptures:")
            parts.extend(verse_texts)

    # Commentary content (truncate if very long)
    if lesson.content:
        max_content_chars = 25000  # ~6K tokens, leaves room for refs
        content = lesson.content[:max_content_chars]
        if len(lesson.content) > max_content_chars:
            content += "..."
        parts.append(f"\nLesson Content:\n{content}")

    return "\n".join(parts)


def get_lessons_without_embeddings(session, lang: str, limit: Optional[int] = None):
    """Get CFM lessons that don't have embeddings yet."""
    query = session.query(CFMLesson).filter(
        CFMLesson.lang == lang,
        CFMLesson.embedding.is_(None)
    ).order_by(CFMLesson.id)

    if limit:
        query = query.limit(limit)

    return query.all()


def process_batch(session, lessons: list[CFMLesson], batch_num: int, total_batches: int):
    """Process a batch of lessons."""
    # Build context texts
    texts = [build_cfm_context(session, lesson) for lesson in lessons]

    # Get embeddings
    embeddings = get_embeddings(texts)

    # Update database
    for lesson, embedding in zip(lessons, embeddings):
        lesson.embedding = embedding

    session.commit()
    print(f"Batch {batch_num}/{total_batches}: Processed {len(lessons)} lessons")


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for CFM lessons")
    parser.add_argument("--lang", choices=["en", "es"], default="en", help="Language")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between batches (seconds)")
    parser.add_argument("--limit", type=int, help="Limit number of lessons to process")
    args = parser.parse_args()

    print(f"Starting CFM embedding generation for {args.lang}...")

    with get_session() as session:
        lessons = get_lessons_without_embeddings(session, args.lang, args.limit)
        total = len(lessons)

        if total == 0:
            print("No lessons without embeddings found.")
            return

        print(f"Found {total} lessons without embeddings")

        total_batches = (total + args.batch_size - 1) // args.batch_size

        for i in range(0, total, args.batch_size):
            batch = lessons[i:i + args.batch_size]
            batch_num = i // args.batch_size + 1

            process_batch(session, batch, batch_num, total_batches)

            if i + args.batch_size < total:
                time.sleep(args.delay)

    print(f"\nCompleted! Generated embeddings for {total} CFM lessons.")


if __name__ == "__main__":
    main()
