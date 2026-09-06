## Problem

`app/__init__.py` hardcodes `logging.DEBUG`:

```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
```

This causes excessive log output in production environments, including:
- SQL query logs
- Debug-level Flask messages
- Third-party library debug output

## Fix

Read log level from environment variable with a safe default:

```python
level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
```

## Acceptance Criteria

- [ ] Default log level is `INFO`
- [ ] `LOG_LEVEL=DEBUG` env var enables debug logging when needed
- [ ] Log format remains unchanged
