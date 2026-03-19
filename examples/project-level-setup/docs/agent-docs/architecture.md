# Architecture

One-line: How this project's codebase is organized.

---

## Source Layout

```
src/
├── core/           ← core business logic
├── api/            ← API endpoints and handlers
├── models/         ← data models and schemas
└── utils/          ← shared utilities
```

## Key Patterns

- **Entry point:** `src/main.py`
- **Config:** Environment variables, loaded via `src/core/config.py`
- **Testing:** `pytest` with fixtures in `tests/conftest.py`

## Dependencies

- Python 3.11+
- Key packages: `<list your key deps>`
- Install: `uv sync` or `pip install -e .`
