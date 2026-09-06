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


@register
class IndexUsageBenchmark(BenchmarkBase):
    name = "index_usage"
    title = "WHERE with index vs without index"
    description = "Demonstrates the impact of B-tree indexes on query performance"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_users_age")
            conn.commit()

    def run(self, conn) -> BenchmarkResult:
        query_no_idx = "SELECT * FROM users WHERE age > %s"
        query_with_idx = "SELECT * FROM users WHERE age > %s"

        thresholds = [20, 30, 40, 50, 60]

        q1_times, q2_times = [], []
        q1_rows, q2_rows = [], []

        with conn.cursor() as cur:
            for t in thresholds:
                rows, elapsed = self._measure(query_no_idx, (t,), cur)
                q1_times.append(elapsed)
                q1_rows.append(rows)

            cur.execute("CREATE INDEX idx_users_age ON users(age)")
            conn.commit()

            for t in thresholds:
                rows, elapsed = self._measure(query_with_idx, (t,), cur)
                q2_times.append(elapsed)
                q2_rows.append(rows)

        q1 = QueryResult(
            name="Without index",
            query=query_no_idx.replace("%s", "20"),
            times=q1_times, limits=thresholds, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name="With B-tree index",
            query=query_with_idx.replace("%s", "20"),
            times=q2_times, limits=thresholds, rows_fetched=q2_rows,
        )

        comparison = self._build_comparison(q1, q2, "age >")
        plot = self._build_plot(q1, q2)

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2], comparison_table=comparison, plot_buffer=plot,
        )

    def teardown(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS idx_users_age")
            conn.commit()

    def _measure(self, query, params, cursor):
        start = time.perf_counter()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000
        return len(rows), elapsed

    def _build_comparison(self, q1, q2, label):
        rows = []
        for i, t in enumerate(q1.limits):
            diff = q1.times[i] - q2.times[i]
            speedup = f"{q1.times[i] / q2.times[i]:.1f}x" if q2.times[i] > 0 else "N/A"
            rows.append({
                f"{label}": t,
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
        ax.set_xlabel("age threshold")
        ax.set_ylabel("Execution Time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
