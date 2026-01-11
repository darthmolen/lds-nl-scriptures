# Bug: Variable shadowing in models.py

## Discovered
2026-01-11 during Task 7 (Verification Script) implementation

## Description
In `src/db/models.py`, line 51 defines a column named `text`:
```python
text = Column(Text, nullable=False)
```

This shadows the imported `text` function from SQLAlchemy, which is used on line 56:
```python
created_at = Column(TIMESTAMP, server_default=text("NOW()"))
```

This causes a `TypeError: 'Column' object is not callable` when importing the models.

## Root Cause
The SQLAlchemy `text()` function and the `Text` type have unfortunately similar names. When the `Scripture` model defines a column attribute named `text`, it overwrites the imported function in the class namespace.

## Fix Options
1. Rename the column attribute to `verse_text` or `content`
2. Use a fully qualified import: `sqlalchemy.text("NOW()")`
3. Import with alias: `from sqlalchemy import text as sql_text`

## Priority
High - blocks all model imports

## Files Affected
- `src/db/models.py` (line 51, 56, 95)
