# TOON Format Summary

**Token-Oriented Object Notation (TOON)** is a compact, human-readable serialization format designed to reduce LLM token usage by 30-60% compared to JSON. It combines YAML-like indentation with CSV-style tabular arrays.

## Why TOON?

LLMs charge by tokens. JSON wastes tokens on:

- Repeated keys in arrays of objects
- Quotation marks and brackets
- Structural punctuation

TOON eliminates this overhead by declaring the schema once and streaming data as CSV-like rows.

**Key benefits:**

- **30-60% fewer tokens** for uniform tabular data
- **Human-readable** - easier to debug than minified JSON
- **Round-trip safe** - TOON to Python to TOON preserves data
- **LLM-friendly** - models understand TOON natively

---

## This Project: LDS Scripture Search

We use TOON to maximize context capacity when uploading scriptures and Come Follow Me content to Claude Projects.

### Conversion Results

| Content | JSON Tokens | TOON Tokens | Savings |
| --------- | ------------- | ------------- | --------- |
| English Scriptures | ~2.9M | ~2.3M | **21-29%** |
| Spanish Scriptures | ~2.6M | ~2.0M | **21-29%** |
| Come Follow Me | ~3.5M | ~3.5M | **0.5%** |
| **Total** | **~9M** | **~7M** | **21.6%** |

**Why scriptures benefit more than CFM:**

- Scriptures are **tabular** (uniform verse records with same fields)
- CFM lessons are **prose** (free-form text doesn't compress well)

### Scripture TOON Structure

```text
[6604]{vol,book,ch,vs,text,fn}:
  volume,1nephi,1,1,"I, Nephi, having been born of goodly parents...","22:26:TG Birthright.|30:36:Prov. 22:1."
  volume,1nephi,1,2,"Yea, I make a record in the language of my father...","28:36:Mosiah 1:4; Morm. 9:32."
  volume,1nephi,1,3,"And I know that the record which I make is true...","43:47:1 Ne. 14:30..."
```

- Header declares count and schema: `[6604]{vol,book,ch,vs,text,fn}:`
- Each verse is one CSV row
- Footnotes compacted: `start:end:reference|start:end:reference`

### Practical Impact

With 200K token Claude Project limit:

- **JSON**: ~22% of scriptures fit
- **TOON**: ~28% of scriptures fit (25% more content)

For a bilingual project, this difference lets you include significantly more reference material.

### File Locations

```text
content/
├── processed/           # Source JSON
│   ├── scriptures/{en,es}/
│   └── cfm/{en,es}/
└── transformed/         # TOON output
    ├── scriptures/{en,es}/*.toon
    └── cfm/{en,es}/*.toon
```

---

## TOON Format Examples

### Simple Object

**JSON:**

```json
{"name": "Alice", "age": 30, "active": true}
```

**TOON:**

```text
name: Alice
age: 30
active: true
```

### Nested Object

**JSON:**

```json
{"user": {"id": 123, "profile": {"city": "Seattle"}}}
```

**TOON:**

```text
user:
  id: 123
  profile:
    city: Seattle
```

### Primitive Array

**JSON:**

```json
{"tags": ["python", "rust", "ml"]}
```

**TOON:**

```text
tags[3]: python,rust,ml
```

### Tabular Array (TOON's Sweet Spot)

**JSON:**

```json
{
  "users": [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"}
  ]
}
```

**TOON:**

```text
users[2,]{id,name,role}:
  1,Alice,admin
  2,Bob,user
```

Schema declared once, then rows stream as CSV. This is where TOON shines.

---

## Token Savings by Data Type

| Data Structure | Typical Savings |
| ---------------- | ----------------- |
| Uniform tabular arrays | 40-60% |
| Nested objects | 20-40% |
| Mixed/irregular data | 10-30% |
| Free-form prose | Minimal |
| Deeply nested structures | Minimal (JSON may be better) |

---

## Python SDK Comparison

| Aspect | **toons** | **toon-python** | **toon-llm** |
| -------- | ----------- | ----------------- | -------------- |
| Install | `pip install toons` | `pip install git+https://github.com/toon-format/toon-python.git` | `pip install toon-llm` |
| Python | 3.7+ | 3.8+ | 3.11+ |
| Implementation | Rust + PyO3 | Pure Python | Pure Python |
| API | `loads()`/`dumps()` | `encode()`/`decode()` | `encode()`/`decode()` |
| Performance | Fastest | Standard | Standard |
| Token Counting | No | Yes | No |
| CLI | No | Yes | Yes |

**This project uses `toons`** for its Rust performance and familiar json-like API.

### Quick Links

| Package | Repository |
| --------- | ------------ |
| **toons** (we use this) | [github.com/alesanfra/toons](https://github.com/alesanfra/toons) |
| **toon-python** (official) | [github.com/toon-format/toon-python](https://github.com/toon-format/toon-python) |
| **toon-llm** | [github.com/davidpirogov/toon-llm](https://github.com/davidpirogov/toon-llm) |

### Basic Usage

```python
import toons

# Parse TOON (like json.loads)
data = toons.loads("""
name: Alice
age: 30
tags[2]: python,ml
""")

# Serialize to TOON (like json.dumps)
print(toons.dumps({"name": "Bob", "age": 25}))
```

---

## References

- **TOON Specification**: [github.com/toon-format/toon](https://github.com/toon-format/toon)
- **Official Website**: [toonformat.dev](https://toonformat.dev/)
- **TypeScript SDK**: [npmjs.com/package/@toon-format/toon](https://www.npmjs.com/package/@toon-format/toon)
