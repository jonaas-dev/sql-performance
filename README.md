<h1 align="center">🔍 SQL Performance Benchmark</h1>

<p align="center">
  <strong>Identify and understand SQL performance issues — with real numbers and EXPLAIN ANALYZE</strong>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-00D26A.svg?style=for-the-badge" alt="License"></a>
  <a href="Dockerfile"><img src="https://img.shields.io/badge/docker-ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="#testing"><img src="https://img.shields.io/badge/tests-33%20passing-brightgreen.svg?style=for-the-badge" alt="Tests"></a>
</p>

---

## What is this?

A toolkit for **detecting and understanding SQL performance problems** — not just measuring them.

Every query has a cost. Some are obvious (SELECT * on a wide table), some are subtle (OFFSET pagination that degrades under load), and some depend on context (JOIN vs subquery vs EXISTS). This tool runs real benchmarks against PostgreSQL, measures the actual impact, and shows you **why** one approach is faster with `EXPLAIN ANALYZE`.

**Built for developers who want data, not opinions.**

---

## Benchmark examples

The toolkit includes several built-in benchmarks that demonstrate common performance patterns. Each one tests a specific scenario, measures execution time across different data sizes, and explains the query plan.

---

### SELECT * vs SELECT columns

> *The most common performance trap*

```sql
-- Fetches all 16 columns
SELECT * FROM users LIMIT 1000000;

-- Fetches only 3 columns
SELECT id, name, email FROM users LIMIT 1000000;
```

**Why it matters**: Every extra column adds I/O, memory, and network overhead. On a table with 16 columns and 1M rows, `SELECT *` transfers **16x more data** than selecting specific columns.

**Typical result**: `SELECT *` is **5-10x slower** on wide tables. The gap grows with table width.

---

### Index usage

> *Why B-tree indexes are not optional*

```sql
-- Full table scan (no index)
SELECT * FROM users WHERE age > 30;

-- Index scan (after CREATE INDEX)
SELECT * FROM users WHERE age > 30;
```

**Why it matters**: Without an index, PostgreSQL reads **every row** in the table. With a B-tree index on the filtered column, it jumps directly to matching rows.

**Typical result**: Indexes speed up filtered queries **100x+**. The larger the table, the bigger the impact.

---

### JOIN vs subquery vs EXISTS

> *Three ways to filter related data*

```sql
-- Pattern 1: JOIN (when you need columns from both tables)
SELECT u.id, u.name, o.amount
FROM users u INNER JOIN orders o ON u.id = o.user_id
WHERE o.amount > 100;

-- Pattern 2: IN subquery (when you only need the main table)
SELECT id, name FROM users
WHERE id IN (SELECT user_id FROM orders WHERE amount > 100);

-- Pattern 3: EXISTS (when you only need to check existence)
SELECT id, name FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 100);
```

**Why it matters**: Each pattern has different performance characteristics depending on data distribution, indexes, and result set size. There is no universal "fastest" — only fastest **for your case**.

---

### OFFSET vs keyset pagination

> *Why `OFFSET 500000` is slow*

```sql
-- OFFSET: must scan and discard all skipped rows
SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 500000;

-- Keyset: jumps directly to position
SELECT * FROM users WHERE id > 500000 ORDER BY id LIMIT 10;
```

**Why it matters**: OFFSET pagination degrades linearly with page number. At page 50,000, PostgreSQL reads 500K rows just to discard them. Keyset pagination stays **constant** regardless of position.

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
| `medium` | 100,000 | Daily benchmarking |
| `large` | 1,000,000 | Serious performance testing |

---

## Architecture

```
sql-performance/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration from .env
│   ├── db.py                # PostgreSQL connection
│   ├── benchmark.py         # Benchmark runner + EXPLAIN ANALYZE
│   ├── history.py           # Historical results storage (filesystem)
│   ├── routes.py            # Flask routes
│   └── templates/           # Jinja2 templates
├── benchmarks/
│   ├── base.py              # BenchmarkBase ABC — all benchmarks extend this
│   ├── registry.py          # Auto-discovery — drop a file, it's registered
│   ├── select_star.py       # SELECT * vs columns
│   ├── index_usage.py       # B-tree index impact
│   ├── join_vs_subquery.py  # JOIN vs IN vs EXISTS
│   └── pagination.py        # OFFSET vs keyset
├── queries/                 # SQL files (loaded by benchmarks)
├── sql/
│   ├── init.sql             # DDL + seed data
│   └── seed.py              # Parametrized seeder (small/medium/large)
├── tests/                   # pytest tests (33 tests)
├── wsgi.py                  # Gunicorn entry point
├── docker-compose.yml       # PostgreSQL + Flask app
└── Dockerfile               # Production container
```

---

## Adding your own benchmark

The plugin architecture makes it easy to add new benchmarks. Here's the full process:

### Step 1: Create a benchmark file

Create a new `.py` file in `benchmarks/` (e.g., `benchmarks/deadlock_demo.py`):

```python
from benchmarks.base import BenchmarkBase, BenchmarkResult, QueryResult
from benchmarks.registry import register

@register
class DeadlockDemo(BenchmarkBase):
    name = "deadlock_demo"
    title = "Deadlock detection patterns"
    description = "Compare LOCK timeout vs row-level locking strategies"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        """Create indexes, temp tables, or test data before the benchmark."""
        with conn.cursor() as cur:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_city ON users(city)")

    def run(self, conn) -> BenchmarkResult:
        """Execute queries, measure times, build results."""
        import time
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from io import BytesIO

        queries = []
        cities = ["New York", "London", "Tokyo", "Berlin", "Sydney"]

        # Measure each city filter
        times = []
        for city in cities:
            start = time.perf_counter()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE city = %s", (city,))
                cur.fetchall()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        queries.append(QueryResult(
            name="Filter by city",
            query="SELECT * FROM users WHERE city = %s",
            times=times,
            limits=cities,
            rows_fetched=1000,
        ))

        # Build comparison table
        comparison = pd.DataFrame({
            "city": cities,
            "time_ms": [round(t, 2) for t in times],
        })

        # Build plot
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(cities, times, marker="o")
        ax.set_xlabel("City")
        ax.set_ylabel("Time (ms)")
        ax.set_title("Deadlock Demo")
        ax.grid(True, alpha=0.3)

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        return BenchmarkResult(
            name=self.name,
            title=self.title,
            description=self.description,
            queries=queries,
            comparison_table=comparison,
            plot_buffer=buf,
            explain_plans={},
        )

    def teardown(self, conn) -> None:
        """Clean up any created objects."""
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_users_city")
```

### Step 2: That's it

The registry auto-discovers new files in `benchmarks/`. No import, no registration code. Just drop the file and restart.

### Step 3: What each method does

| Method | Purpose | Examples |
|--------|---------|----------|
| `setup(conn)` | Prepare the database before measuring | Create indexes, temp tables, seed test data |
| `run(conn)` | Execute queries, measure times, return results | Run queries with `time.perf_counter()`, build plot |
| `teardown(conn)` | Clean up after the benchmark | Drop indexes, temp tables |

### Step 4: Required attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `name` | `str` | Unique identifier (used in URL: `?benchmark=name`) |
| `title` | `str` | Human-readable name (shown in UI) |
| `description` | `str` | What this benchmark tests |
| `required_tables` | `list[str]` | Tables that must exist before setup |

### Step 5: Return value

Your `run()` method must return a `BenchmarkResult` with:

- **`queries`**: List of `QueryResult` objects (name, query text, execution times, data points)
- **`comparison_table`**: A pandas DataFrame shown in the UI table
- **`plot_buffer`**: A `BytesIO` containing a PNG image (the chart)
- **`explain_plans`**: Dict of query name → EXPLAIN ANALYZE text (optional, auto-collected if empty)

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

**33 tests** covering registry discovery, benchmark metadata, plot generation, config, history, and routes.

---

## License

[MIT](LICENSE) — use it, fork it, learn from it.
