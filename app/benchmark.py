import base64
import logging

from benchmarks import all, default, get
from benchmarks.base import BenchmarkResult

logger = logging.getLogger(__name__)


def run_explain(conn, query: str, params=None) -> str:
    with conn.cursor() as cur:
        explain_query = f"EXPLAIN ANALYZE {query}"
        cur.execute(explain_query, params)
        return "\n".join(row[0] for row in cur.fetchall())


def run_benchmark(conn, benchmark_name: str | None = None) -> BenchmarkResult:
    if benchmark_name:
        bm = get(benchmark_name)
        if bm is None:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
    else:
        bm = default()

    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    if not result.explain_plans:
        result.explain_plans = _collect_explain_plans(conn, result)

    return result


def _collect_explain_plans(conn, result: BenchmarkResult) -> dict[str, str]:
    plans = {}
    for q in result.queries:
        try:
            plans[q.name] = run_explain(conn, q.query)
        except Exception as e:
            logger.warning("EXPLAIN failed for %s: %s", q.name, e)
            plans[q.name] = f"Error: {e}"
    return plans


def result_to_plot_data(result: BenchmarkResult) -> str:
    return base64.b64encode(result.plot_buffer.getvalue()).decode("utf-8")


def list_benchmarks() -> list[dict]:
    return [
        {"name": bm.name, "title": bm.title, "description": bm.description}
        for bm in all()
    ]
