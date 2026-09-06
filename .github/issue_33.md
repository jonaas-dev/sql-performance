## Problem

`requirements.txt` lists packages without version constraints:

```
psycopg2-binary
flask
gunicorn
matplotlib
pandas
```

This means:
- Future incompatible releases can break the project
- Installations are not reproducible
- CI builds may fail unexpectedly

## Fix

Pin to current stable versions:
```
psycopg2-binary==2.9.9
flask==3.0.3
gunicorn==23.0.0
matplotlib==3.9.2
pandas==2.2.2
```

## Acceptance Criteria

- [ ] All production dependencies have pinned versions
- [ ] `pip install -r requirements.txt` produces deterministic installs
- [ ] Application still runs correctly with pinned versions
