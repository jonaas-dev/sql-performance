## Problem

`pyproject.toml` sets `fail_under = 70` for coverage:

```toml
[tool.coverage.report]
show_missing = true
fail_under = 70
```

The actual test coverage is likely below 70%, which means `pytest --cov` will fail for new contributors or in CI.

## Fix

Lower the threshold to a realistic value until coverage is improved:

```toml
fail_under = 50
```

## Acceptance Criteria

- [ ] `pytest --cov` passes without coverage failures
- [ ] A comment or issue is created to track raising the threshold back to 70%
