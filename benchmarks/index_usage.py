import io

import matplotlib

matplotlib.use("Agg")
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.benchmark import run_explain
from benchmarks.base import (
    BenchmarkBase,
    BenchmarkResult,
    QueryResult,
    measure,
)
from benchmarks.registry import register

QUERY = "SELECT * FROM users WHERE age = %s"
INDEX_NAME = "sqlperf_idx_users_age"
THRESHOLDS = [25, 30, 35, 40, 45]
EXPLAIN_AGE = 35

NO_INDEX_LABEL = "Seq Scan (no index)"
WITH_INDEX_LABEL = "Index Scan (with B-tree)"


@register
class IndexUsageBenchmark(BenchmarkBase):
    name = "index_usage"
    title = "WHERE with index vs without index"
    description = "Demonstrates the impact of B-tree indexes on query performance"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        self.check_requirements(conn)
        with conn.cursor() as cur:
            cur.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
            conn.commit()

    def run(self, conn) -> BenchmarkResult:
        q1_times, q1_rows = [], []
        q2_times, q2_rows = [], []

        with conn.cursor() as cur:
            for age in THRESHOLDS:
                rows, elapsed = measure(cur, QUERY, (age,))
                q1_times.append(elapsed)
                q1_rows.append(rows)

        # Captured before the index exists: running both EXPLAINs after
        # CREATE INDEX makes them identical and the "no index" label a lie.
        no_index_plan = run_explain(conn, QUERY, (EXPLAIN_AGE,))

        with conn.cursor() as cur:
            cur.execute(f"CREATE INDEX {INDEX_NAME} ON users(age)")
            cur.execute("ANALYZE users")
            conn.commit()

            for age in THRESHOLDS:
                rows, elapsed = measure(cur, QUERY, (age,))
                q2_times.append(elapsed)
                q2_rows.append(rows)

        with_index_plan = run_explain(conn, QUERY, (EXPLAIN_AGE,))

        q1 = QueryResult(
            name=NO_INDEX_LABEL, query=QUERY,
            times=q1_times, limits=THRESHOLDS, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name=WITH_INDEX_LABEL, query=QUERY,
            times=q2_times, limits=THRESHOLDS, rows_fetched=q2_rows,
        )

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2],
            comparison_table=self._build_comparison(q1, q2),
            plot_buffer=self._build_plot(q1, q2),
            explain_plans={q1.name: no_index_plan, q2.name: with_index_plan},
        )

    def teardown(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
            conn.commit()

    def _build_comparison(self, q1, q2):
        rows = []
        for i, age in enumerate(q1.limits):
            speedup = f"{q1.times[i] / q2.times[i]:.1f}x" if q2.times[i] > 0 else "N/A"
            rows.append({
                "age =": age,
                "rows_matched": q1.rows_fetched[i],
                "without_index": f"{q1.times[i]:.2f} ms",
                "with_index": f"{q2.times[i]:.2f} ms",
                "speedup": speedup,
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name, color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name, color="#2ecc71")
        ax.set_title(self.title)
        ax.set_xlabel("age = value")
        ax.set_ylabel("Median execution time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
