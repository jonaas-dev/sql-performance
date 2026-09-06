<h1 align="center">🔍 SQL Performance Benchmark</h1>

<p align="center">
  <strong>Find out why your queries are slow — with real numbers and EXPLAIN ANALYZE</strong>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-00D26A.svg?style=for-the-badge" alt="License"></a>
  <a href="Dockerfile"><img src="https://img.shields.io/badge/docker-ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="#testing"><img src="https://img.shields.io/badge/tests-33%20✓-brightgreen.svg?style=for-the-badge" alt="Tests"></a>
</p>

---

## What is this?

A benchmarking toolkit that tests **4 real-world SQL patterns** and shows you **why** one is faster — not just that it is.

Each benchmark runs against PostgreSQL, measures execution time, generates a visual comparison, and explains the query plan with `EXPLAIN ANALYZE`.

**Not another SELECT * demo.** This is a toolkit for developers who want to understand PostgreSQL performance with data, not opinions.

---

## The 4 benchmarks

<table>
<tr>
<td width="50%">

### 📊 SELECT * vs columns

> *The classic performance trap*

```sql
-- Slow: fetches all 16 columns
SELECT * FROM users LIMIT 1000000;

-- Fast: fetches only 3
SELECT id, name, email FROM users LIMIT 1000000;
```

**Result**: `SELECT *` is **5-10x slower** on wide tables.

Every extra column adds I/O, memory, and network overhead. This benchmark makes the gap visible.

</td>
<td width="50%">

### ⚡ Index usage

> *Why B-tree indexes are not optional*

```sql
-- Slow: full table scan
SELECT * FROM users WHERE age > 30;

-- Fast: index scan (after CREATE INDEX)
SELECT * FROM users WHERE age > 30;
```

**Result**: Indexes speed up queries **100x+**.

Without an index, PostgreSQL reads every row. With one, it jumps directly to matching rows.

</td>
</tr>
<tr>
<td>

### 🔗 JOIN vs subquery vs EXISTS

> *Three ways to filter related data*

```sql
-- Pattern 1: JOIN
SELECT u.* FROM users u
JOIN orders o ON u.id = o.user_id;

-- Pattern 2: IN (subquery)
SELECT * FROM users
WHERE id IN (SELECT user_id FROM orders);

-- Pattern 3: EXISTS
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o
              WHERE o.user_id = u.id);
```

Each pattern has different performance characteristics depending on data distribution and indexes.

</td>
<td>

### 📄 OFFSET vs keyset pagination

> *Why `OFFSET 500000` is slow*

```sql
-- Slow: must scan and discard 500K rows
SELECT * FROM users
ORDER BY id LIMIT 10 OFFSET 500000;

-- Fast: jumps directly to position
SELECT * FROM users
WHERE id > 500000
ORDER BY id LIMIT 10;
```

**Result**: OFFSET degrades linearly. Keyset stays **constant**.

</td>
</tr>
</table>

---

## Screenshots

<p align="center">
  <img src="./app/img/comparation_table.png" alt="Benchmark comparison" width="800">
  <br>
  <em>Visual comparison of query execution times with EXPLAIN ANALYZE output</em>
</p>

---

## Quick start

```bash
git clone https://github.com/jonaas-dev/sql-performance.git
cd sql-performance
cp .env.example .env
docker-compose up --build
```

Open **http://localhost:8000**, select a benchmark, choose dataset size, and click **Generate**.

### Dataset sizes

| Size | Rows | Use case |
|------|------|----------|
| `small` | 10,000 | Development, quick tests |
| `medium` | 100,000 | Daily benchmarks |
| `large` | 1,000,000 | Serious performance testing |

---

## Architecture

```
sql-performance/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration from .env
│   ├── db.py                # PostgreSQL connection
│   ├── benchmark.py         # Benchmark runner + EXPLAIN
│   ├── history.py           # Historical results storage
│   ├── routes.py            # Flask routes
│   └── templates/           # Jinja2 templates
├── benchmarks/
│   ├── base.py              # BenchmarkBase ABC
│   ├── registry.py          # Auto-discovery registry
│   ├── select_star.py       # SELECT * vs columns
│   ├── index_usage.py       # Index impact demo
│   ├── join_vs_subquery.py  # JOIN vs IN vs EXISTS
│   └── pagination.py        # OFFSET vs keyset
├── sql/
│   ├── init.sql             # DDL + seed data
│   └── seed.py              # Parametrized seeder
├── tests/                   # pytest tests (33 tests)
├── wsgi.py                  # Gunicorn entry point
├── docker-compose.yml       # Full stack setup
└── Dockerfile               # Production container
```

---

## Adding your own benchmark

Create a file in `benchmarks/` and extend `BenchmarkBase`:

```python
from benchmarks.base import BenchmarkBase, BenchmarkResult, QueryResult
from benchmarks.registry import register

@register
class MyBenchmark(BenchmarkBase):
    name = "my_benchmark"
    title = "My custom benchmark"
    description = "What this tests"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        # Create indexes, temp tables, etc.
        pass

    def run(self, conn) -> BenchmarkResult:
        # Run queries, measure times, build results
        pass

    def teardown(self, conn) -> None:
        # Clean up
        pass
```

It's auto-discovered — no registration code needed.

---

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `user` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `DB_NAME` | `test_db` | Database name |
| `DB_SEED_SIZE` | `medium` | Dataset size (`small`/`medium`/`large`) |

---

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /` | Landing page with benchmark selector |
| `GET /generate?benchmark=<name>&size=<size>` | Run a benchmark |
| `GET /history` | List all historical benchmark runs |
| `GET /results/<id>` | View a specific historical result |

---

## Testing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app
```

**33 tests** covering registry, benchmarks, config, history, and routes.

---

## License

[MIT](LICENSE) — use it, fork it, learn from it.
