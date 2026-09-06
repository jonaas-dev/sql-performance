## Security Issue

`wsgi.py` hardcodes `debug=True`:

```python
if __name__ == '__main__':
    app.run(debug=True)
```

Running `python wsgi.py` directly exposes the Werkzeug interactive debugger, which allows remote code execution if an exception occurs.

## Fix

Read from environment variable with safe defaults:

```python
import os

if __name__ == '__main__':
    app.run(
        debug=os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes"),
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", "5000")),
    )
```

## Acceptance Criteria

- [ ] Default behavior runs with `debug=False`
- [ ] `FLASK_DEBUG=true` enables debug mode when explicitly set
- [ ] `FLASK_PORT` env var configures the port
