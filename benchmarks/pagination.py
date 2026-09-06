import time
import io
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd

from benchmarks.base import BenchmarkBase, BenchmarkResult, QueryResult
from benchmarks.registry import register
from app.config import TMP_DIR
from app.benchmark import run_explain


@register
class PaginationBenchmark(BenchmarkBase):
    name = "pagination"
    title = "OFFSET vs keyset pagination"
    description = "Demonstrates why OFFSET degrades at high page numbers and keyset stays constant"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_users_id_cursor")
            cur.execute("CREATE INDEX idx_users_id_cursor ON users(id)")
            conn.commit()

    def run(self, conn) -> BenchmarkResult:
        page_sizes = [100, 500, 1000, 5000, 10000]

        q1_times, q2_times = [], []
        q1_rows, q2_rows = [], []

        with conn.cursor() as cur:
            for page_size in page_sizes:
                offset = 500000

                query_offset = "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s"
                rows, t1 = self._measure(query_offset, cur, (page_size, offset))
                q1_times.append(t1)
                q1_rows.append(rows)

                query_keyset = "SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s"
                rows, t2 = self._measure(query_keyset, cur, (offset, page_size))
                q2_times.append(t2)
                q2_rows.append(rows)

        q1 = QueryResult(
            name="OFFSET", query="SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s",
            times=q1_times, limits=page_sizes, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name="Keyset (WHERE id >)", query="SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s",
            times=q2_times, limits=page_sizes, rows_fetched=q2_rows,
        )

        comparison = self._build_comparison(q1, q2)
        plot = self._build_plot(q1, q2)

        explain_plans = {
            q1.name: run_explain(conn, "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s", (100, 500000)),
            q2.name: run_explain(conn, "SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s", (500000, 100)),
        }

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2], comparison_table=comparison, plot_buffer=plot,
            explain_plans=explain_plans,
        )

    def teardown(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_users_id_cursor")
            conn.commit()

    def _measure(self, query, cursor, params=None):
        start = time.perf_counter()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000
        return len(rows), elapsed

    def _build_comparison(self, q1, q2):
        rows = []
        for i, limit in enumerate(q1.limits):
            diff = q1.times[i] - q2.times[i]
            rows.append({
                "page_size": limit,
                "offset": f"{q1.times[i]:.2f} ms",
                "keyset": f"{q2.times[i]:.2f} ms",
                "diff": f"{diff:.2f} ms",
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name, color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name, color="#2ecc71")
        ax.set_title(self.title)
        ax.set_xlabel("Page size (OFFSET at 500K)")
        ax.set_ylabel("Execution Time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
