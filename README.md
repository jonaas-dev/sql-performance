# SQL Performance: SELECT * vs SELECT columns

A visual benchmarking tool that demonstrates why `SELECT * FROM table` is slow and `SELECT col1, col2 FROM table` is fast — with real numbers.

## Why this matters

Every `SELECT *` fetches every column, every row. When your table has 16 columns and 1M rows, that's 16x more data than `SELECT 1,2,3`. The difference isn't theoretical:

| LIMIT | SELECT * (Query 1) | SELECT 1,2,3 (Query 2) | Difference |
|------:|-------------------:|-----------------------:|-----------:|
| 1,000,000 | ~1500ms | ~200ms | **7.5x faster** |
| 500,000 | ~750ms | ~100ms | **7.5x faster** |

This tool makes that gap visible with a side-by-side benchmark and a clean comparison table.

## Quick start

```bash
git clone https://github.com/jonaas-dev/sql-performance.git
cd sql-performance
cp .env.example .env
docker-compose up --build
```

Open `http://localhost:8000` and click **Generate**.

## How it works

1. PostgreSQL spins up with 1M rows of synthetic data
2. Query 1: `SELECT * FROM users LIMIT n` (fetches all 16 columns)
3. Query 2: `SELECT 1,2,3 FROM users LIMIT n` (returns 3 constants)
4. Each query runs at decreasing LIMITs (1M → 100k, step 100k)
5. Execution times are measured, plotted, and compared in a table

## Configuration

All settings via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `user` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `DB_NAME` | `test_db` | Database name |

## Project structure

```
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── config.py         # Configuration from .env
│   ├── db.py             # PostgreSQL connection
│   ├── benchmark.py      # Core benchmarking logic
│   ├── routes.py         # Flask routes
│   ├── templates/        # Jinja2 templates
│   └── static/           # CSS
├── queries/              # SQL files to benchmark
├── sql/                  # Database initialization
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

## Screenshots

Query execution results:

![Query execution results](./app/img/query_execution_results.png)

Comparison table:

![Comparison table](./app/img/comparation_table.png)

## License

MIT — see [LICENSE](LICENSE) for details.
