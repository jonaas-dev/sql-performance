# SQL Performance Benchmark

A visual benchmarking tool that demonstrates why `SELECT * FROM table` is slow and selecting specific columns is fast — with real numbers and EXPLAIN ANALYZE.

## Why this matters

Every `SELECT *` fetches every column, every row. When your table has 16 columns and 1M rows, that's 16x more data than selecting specific columns. The difference isn't theoretical — this tool makes it visible.

## Benchmarks

| Benchmark | What it tests | Key insight |
|-----------|---------------|-------------|
| **SELECT * vs columns** | Fetching all columns vs specific ones | `SELECT *` is 5-10x slower on wide tables |
| **Index usage** | WHERE with/without B-tree index | Indexes can speed up queries 100x+ |
| **JOIN vs subquery** | JOIN, IN, EXISTS patterns | Each pattern has different performance characteristics |
| **Pagination** | OFFSET vs keyset (WHERE id >) | OFFSET degrades at high page numbers |

## Quick start

```bash
git clone https://github.com/jonaas-dev/sql-performance.git
cd sql-performance
cp .env.example .env
docker-compose up --build
```

Open `http://localhost:8000`, select a benchmark, choose dataset size, and click **Generate**.

## Features

### 4 Benchmarks
- **SELECT * vs columns**: The classic performance trap
- **Index usage**: Demonstrates B-tree index impact on filtered queries
- **JOIN vs subquery**: Compares three relational filtering patterns
- **Pagination**: OFFSET vs keyset at high page numbers

### EXPLAIN ANALYZE
Every benchmark shows the PostgreSQL query plan — not just timing, but **why** one query is faster. See Seq Scan vs Index Scan, cost estimation, and row estimates.

### Configurable dataset
Choose between small (10K), medium (100K), or large (1M) rows. Use small for development, large for serious benchmarking.

### Historical results
Every benchmark run is saved with timestamp. Compare results over time via the `/history` endpoint.

### Plugin architecture
Adding a new benchmark is easy — create a file in `benchmarks/`, extend `BenchmarkBase`, and it's auto-discovered.

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `user` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `DB_NAME` | `test_db` | Database name |
| `DB_SEED_SIZE` | `medium` | Dataset size (small/medium/large) |

## Project structure

```
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # Configuration from .env
│   ├── db.py             # PostgreSQL connection
│   ├── benchmark.py      # Benchmark runner + EXPLAIN
│   ├── history.py        # Historical results storage
│   ├── routes.py         # Flask routes
│   └── templates/        # Jinja2 templates
├── benchmarks/
│   ├── base.py           # BenchmarkBase ABC
│   ├── registry.py       # Auto-discovery registry
│   ├── select_star.py    # SELECT * vs columns
│   ├── index_usage.py    # Index impact demo
│   ├── join_vs_subquery.py  # JOIN vs IN vs EXISTS
│   └── pagination.py     # OFFSET vs keyset
├── sql/
│   ├── init.sql          # DDL + seed data
│   └── seed.py           # Parametrized seeder
├── tests/                # pytest tests
├── wsgi.py               # Gunicorn entry point
├── docker-compose.yml    # Full stack setup
└── Dockerfile            # Production container
```

## Running tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=app
```

## Endpoints

| Route | Description |
|-------|-------------|
| `GET /` | Landing page with benchmark selector |
| `GET /generate?benchmark=<name>&size=<size>` | Run a benchmark |
| `GET /history` | List all historical benchmark runs |
| `GET /results/<id>` | View a specific historical result |

## License

MIT — see [LICENSE](LICENSE) for details.
