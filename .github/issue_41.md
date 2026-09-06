## Problem

`sql/seed.py` uses `print()` statements instead of the logging module:

```python
print(f"Database already has {existing} rows (>= {n}), skipping seed.")
print(f"  Inserted {i}/{n} rows...")
print(f"Seeded {n} rows into users table.")
```

This is inconsistent with the rest of the codebase which uses `logging`.

## Fix

Replace `print()` calls with `logging.info()`:

```python
import logging
logger = logging.getLogger(__name__)
# ...
logger.info("Database already has %s rows (>= %s), skipping seed.", existing, n)
```

## Acceptance Criteria

- [ ] No `print()` statements remain in `sql/seed.py`
- [ ] Seed script output is still visible when run directly
- [ ] Logging configuration in `__init__.py` covers `sql.seed`
