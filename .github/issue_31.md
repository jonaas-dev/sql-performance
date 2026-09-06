## Security Issue

The `pagination.py` benchmark constructs SQL queries using f-strings with user-influenced values:

```python
query_offset = f"SELECT * FROM users ORDER BY id LIMIT {page_size} OFFSET {offset}"
query_keyset = f"SELECT * FROM users WHERE id > {offset} ORDER BY id LIMIT {page_size}"
```

While the values come from hardcoded lists in this case, this pattern:
1. Will be flagged by security scanners (GitHub CodeQL, SonarQube)
2. Sets a bad example in a repo about SQL performance
3. Could become vulnerable if the benchmark is ever modified to accept external input

## Fix

Use parameterized queries with `%s` placeholders:
```python
query_offset = "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s"
cursor.execute(query_offset, (page_size, offset))
```

Same fix for the EXPLAIN ANALYZE calls.

## Acceptance Criteria

- [ ] No f-string SQL construction in `benchmarks/pagination.py`
- [ ] All queries use parameterized execution
- [ ] Benchmark output remains identical
