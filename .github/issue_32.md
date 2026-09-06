## Security Issue

The `/generate` route exposes raw database exception messages directly to the user:

```python
except Exception as e:
    logger.exception("Benchmark failed")
    error=str(e)
```

This leaks information about:
- Database connection details
- Table structures
- File paths
- Internal error states

## Fix

Log the full error for debugging, but show a generic message to users:

```python
except Exception as e:
    logger.exception("Benchmark failed: %s", e)
    error = "Database connection failed. Please check your configuration and try again."
```

## Acceptance Criteria

- [ ] Full error details are logged server-side
- [ ] Users see only generic, non-revealing error messages
- [ ] Tests verify generic error message is returned
