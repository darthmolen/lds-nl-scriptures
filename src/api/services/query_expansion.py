"""Query expansion with theological synonyms for improved scripture search.

This module expands search queries by adding related theological terms,
helping match verses that use different vocabulary for the same concepts.
"""

# Theological synonym mappings
# Format: trigger_term -> [additional_terms_to_add]
# Terms are lowercase for matching
THEOLOGICAL_SYNONYMS = {
    # Divine names and titles
    "lamb of god": ["lamb", "sacrifice", "messiah", "christ", "redeemer", "paschal"],
    "i am": ["jehovah", "lord", "yahweh"],
    "the word": ["logos", "christ", "beginning"],
    "son of god": ["christ", "jesus", "messiah", "savior"],
    "holy ghost": ["spirit", "comforter", "holy spirit"],
    "holy spirit": ["ghost", "comforter", "holy ghost"],

    # Book of Mormon specific terms
    "liahona": ["compass", "director", "ball", "curious workmanship"],
    "urim and thummim": ["seer stones", "interpreters", "spectacles"],
    "brass plates": ["plates", "scriptures", "records"],
    "gold plates": ["plates", "records", "book of mormon"],
    "tree of life": ["tree", "fruit", "love of god"],

    # Doctrinal concepts
    "atonement": ["sacrifice", "redemption", "reconciliation", "suffering"],
    "repentance": ["repent", "forgiveness", "turn", "forsake"],
    "baptism": ["baptize", "water", "immersion", "ordinance"],
    "resurrection": ["rise", "risen", "raised", "immortality"],
    "faith": ["believe", "trust", "hope"],
    "charity": ["love", "pure love", "compassion"],
    "priesthood": ["authority", "power", "ordain", "keys"],
    "covenant": ["promise", "oath", "agreement", "testament"],

    # Kingdoms of glory
    "celestial": ["celestial kingdom", "highest", "glory"],
    "terrestrial": ["terrestrial kingdom", "middle"],
    "telestial": ["telestial kingdom", "lowest"],

    # Other theological terms
    "grace": ["mercy", "favor", "gift"],
    "justification": ["justify", "justified", "righteous"],
    "sanctification": ["sanctify", "holy", "pure"],
    "salvation": ["save", "saved", "redeem", "eternal life"],
    "damnation": ["damn", "damned", "perdition", "hell"],
}


def expand_query(query: str) -> str:
    """Expand a query with theological synonyms.

    Looks for known theological terms in the query and adds
    related terms to improve recall.

    Args:
        query: Original search query

    Returns:
        Expanded query with additional terms

    Example:
        >>> expand_query("Lamb of God sacrifice")
        'Lamb of God sacrifice lamb messiah christ redeemer paschal'
    """
    query_lower = query.lower()
    additional_terms = set()

    # Check each synonym mapping
    for trigger, synonyms in THEOLOGICAL_SYNONYMS.items():
        if trigger in query_lower:
            additional_terms.update(synonyms)

    # Add unique terms that aren't already in the query
    for term in list(additional_terms):
        if term.lower() in query_lower:
            additional_terms.discard(term)

    if additional_terms:
        return f"{query} {' '.join(additional_terms)}"
    return query


def get_expansion_terms(query: str) -> list[str]:
    """Get list of expansion terms for a query (for debugging/logging).

    Args:
        query: Original search query

    Returns:
        List of terms that would be added
    """
    query_lower = query.lower()
    additional_terms = set()

    for trigger, synonyms in THEOLOGICAL_SYNONYMS.items():
        if trigger in query_lower:
            additional_terms.update(synonyms)

    # Remove terms already in query
    for term in list(additional_terms):
        if term.lower() in query_lower:
            additional_terms.discard(term)

    return sorted(additional_terms)
