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
    format_ms,
    measure,
    plot_server_series,
    speedup,
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
        m1, m2 = [], []

        with conn.cursor() as cur:
            for age in THRESHOLDS:
                m1.append(measure(cur, QUERY, (age,)))

        # Captured before the index exists: running both EXPLAINs after
        # CREATE INDEX makes them identical and the "no index" label a lie.
        no_index_plan = run_explain(conn, QUERY, (EXPLAIN_AGE,))

        with conn.cursor() as cur:
            cur.execute(f"CREATE INDEX {INDEX_NAME} ON users(age)")
            cur.execute("ANALYZE users")
            conn.commit()

            for age in THRESHOLDS:
                m2.append(measure(cur, QUERY, (age,)))

        with_index_plan = run_explain(conn, QUERY, (EXPLAIN_AGE,))

        q1 = QueryResult(
            name=NO_INDEX_LABEL, query=QUERY, limits=THRESHOLDS,
            times=[m.wall_ms for m in m1], rows_fetched=[m.rows_fetched for m in m1],
            server_times=[m.server_ms for m in m1],
        )
        q2 = QueryResult(
            name=WITH_INDEX_LABEL, query=QUERY, limits=THRESHOLDS,
            times=[m.wall_ms for m in m2], rows_fetched=[m.rows_fetched for m in m2],
            server_times=[m.server_ms for m in m2],
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
            rows.append({
                "age =": age,
                "rows": q1.rows_fetched[i],
                "no index (total)": format_ms(q1.times[i]),
                "no index (server)": format_ms(q1.server_times[i]),
                "indexed (total)": format_ms(q2.times[i]),
                "indexed (server)": format_ms(q2.server_times[i]),
                "speedup (total)": speedup(q1.times[i], q2.times[i]),
                "speedup (server)": speedup(q1.server_times[i], q2.server_times[i]),
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=f"{q1.name} — total", color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=f"{q2.name} — total", color="#2ecc71")
        plot_server_series(ax, q1, "#e74c3c")
        plot_server_series(ax, q2, "#2ecc71")
        ax.set_title(f"{self.title} — solid: total, dashed: PostgreSQL only")
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
