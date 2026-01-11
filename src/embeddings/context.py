"""Context window builder for scripture embeddings."""
from typing import Optional
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from src.db.models import Scripture

# Book ID to display name mapping
BOOK_TITLES = {
    # Book of Mormon
    "1nephi": "1 Nephi", "2nephi": "2 Nephi", "jacob": "Jacob",
    "enos": "Enos", "jarom": "Jarom", "omni": "Omni",
    "wordsofmormon": "Words of Mormon", "mosiah": "Mosiah",
    "alma": "Alma", "helaman": "Helaman", "3nephi": "3 Nephi",
    "4nephi": "4 Nephi", "mormon": "Mormon", "ether": "Ether",
    "moroni": "Moroni",
    # Old Testament (abbreviated list - add more as needed)
    "genesis": "Genesis", "exodus": "Exodus", "leviticus": "Leviticus",
    "numbers": "Numbers", "deuteronomy": "Deuteronomy",
    "joshua": "Joshua", "judges": "Judges", "ruth": "Ruth",
    "1samuel": "1 Samuel", "2samuel": "2 Samuel",
    "1kings": "1 Kings", "2kings": "2 Kings",
    "1chronicles": "1 Chronicles", "2chronicles": "2 Chronicles",
    "ezra": "Ezra", "nehemiah": "Nehemiah", "esther": "Esther",
    "job": "Job", "psalms": "Psalms", "proverbs": "Proverbs",
    "ecclesiastes": "Ecclesiastes", "songofsolomon": "Song of Solomon",
    "isaiah": "Isaiah", "jeremiah": "Jeremiah", "lamentations": "Lamentations",
    "ezekiel": "Ezekiel", "daniel": "Daniel", "hosea": "Hosea",
    "joel": "Joel", "amos": "Amos", "obadiah": "Obadiah",
    "jonah": "Jonah", "micah": "Micah", "nahum": "Nahum",
    "habakkuk": "Habakkuk", "zephaniah": "Zephaniah",
    "haggai": "Haggai", "zechariah": "Zechariah", "malachi": "Malachi",
    # New Testament
    "matthew": "Matthew", "mark": "Mark", "luke": "Luke", "john": "John",
    "acts": "Acts", "romans": "Romans", "1corinthians": "1 Corinthians",
    "2corinthians": "2 Corinthians", "galatians": "Galatians",
    "ephesians": "Ephesians", "philippians": "Philippians",
    "colossians": "Colossians", "1thessalonians": "1 Thessalonians",
    "2thessalonians": "2 Thessalonians", "1timothy": "1 Timothy",
    "2timothy": "2 Timothy", "titus": "Titus", "philemon": "Philemon",
    "hebrews": "Hebrews", "james": "James", "1peter": "1 Peter",
    "2peter": "2 Peter", "1john": "1 John", "2john": "2 John",
    "3john": "3 John", "jude": "Jude", "revelation": "Revelation",
    # D&C and Pearl of Great Price
    "doctrineandcovenants": "D&C", "moses": "Moses",
    "abraham": "Abraham", "josephsmith-matthew": "JS-Matthew",
    "josephsmith-history": "JS-History", "articlesoffaith": "Articles of Faith",
}

def format_book_title(book_id: str) -> str:
    """Convert book ID to display title."""
    return BOOK_TITLES.get(book_id, book_id.title())

def get_context_verses(
    session: Session,
    verse: Scripture,
    context_size: int = 2
) -> tuple[list[Scripture], list[Scripture]]:
    """Get surrounding verses within the same chapter.

    Args:
        session: Database session
        verse: The target verse
        context_size: Number of verses before/after (default: 2)

    Returns:
        Tuple of (previous_verses, next_verses)
    """
    # Get previous verses in same chapter
    prev_verses = session.query(Scripture).filter(
        Scripture.volume == verse.volume,
        Scripture.book == verse.book,
        Scripture.chapter == verse.chapter,
        Scripture.lang == verse.lang,
        Scripture.verse < verse.verse,
        Scripture.verse >= verse.verse - context_size
    ).order_by(Scripture.verse).all()

    # Get next verses in same chapter
    next_verses = session.query(Scripture).filter(
        Scripture.volume == verse.volume,
        Scripture.book == verse.book,
        Scripture.chapter == verse.chapter,
        Scripture.lang == verse.lang,
        Scripture.verse > verse.verse,
        Scripture.verse <= verse.verse + context_size
    ).order_by(Scripture.verse).all()

    return prev_verses, next_verses

def build_context_text(
    verse: Scripture,
    prev_verses: list[Scripture],
    next_verses: list[Scripture]
) -> str:
    """Build hybrid context text for embedding.

    Format: "Book Chapter:StartVerse-EndVerse: [concatenated verse texts]"

    Example: "1 Nephi 1:1-3: I, Nephi... Yea, I make... And I know..."
    """
    # Collect all verses in order
    all_verses = prev_verses + [verse] + next_verses

    # Determine verse range
    start_verse = all_verses[0].verse
    end_verse = all_verses[-1].verse

    # Build reference string
    book_title = format_book_title(verse.book)
    if start_verse == end_verse:
        ref = f"{book_title} {verse.chapter}:{start_verse}"
    else:
        ref = f"{book_title} {verse.chapter}:{start_verse}-{end_verse}"

    # Concatenate verse texts
    text = " ".join(v.text for v in all_verses)

    return f"{ref}: {text}"

def build_context_for_verse(session: Session, verse: Scripture) -> str:
    """Build context text for a single verse, fetching surrounding verses."""
    prev_verses, next_verses = get_context_verses(session, verse)
    return build_context_text(verse, prev_verses, next_verses)
