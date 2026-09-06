# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
docker compose up -d db
psql "postgresql://user:password@localhost:5432/test_db" -f sql/init.sql
```

## Before opening a PR

```bash
ruff check .
pytest --cov
```

Both run in CI against a real PostgreSQL service, so integration tests will not be skipped there.

## Adding a benchmark

See [Adding your own benchmark](README.md#adding-your-own-benchmark). The rules that matter:

- **Use `measure()`** from `benchmarks.base` — it does the warm-up and the median. Hand-rolled
  `time.perf_counter()` around a single run reintroduces the cold-cache bias.
- **Derive your data points from `table_row_count(conn)`**, never hardcode them. A benchmark whose
  parameters exceed the dataset silently measures an empty result set.
- **Prefix any object you create with `sqlperf_`** and drop it in `teardown()`. The tool must never
  destroy a table it did not create.
- **Raise `BenchmarkNotApplicable`** when the dataset is too small for your benchmark to mean
  anything, instead of returning a chart built on nothing.

Every benchmark is automatically covered by the integration suite, which asserts that it fetches a
non-empty result set. If your benchmark cannot satisfy that, it is measuring the wrong thing.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `chore:`, `docs:`,
`test:`. Keep PRs small.
