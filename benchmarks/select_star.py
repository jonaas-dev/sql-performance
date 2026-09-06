import time
import io
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd

from benchmarks.base import BenchmarkBase, BenchmarkResult, QueryResult
from benchmarks.registry import register
from app.config import START, STEP, QUERY_1_NAME, QUERY_2_NAME, TMP_DIR, QUERIES_DIR


@register
class SelectStarBenchmark(BenchmarkBase):
    name = "select_star"
    title = "SELECT * vs SELECT columns"
    description = "Demonstrates why SELECT * is slow and selecting specific columns is fast"
    required_tables = ["users"]

    def _get_query(self, filename: str) -> str:
        with open(QUERIES_DIR / filename) as f:
            return f.read()

    def _measure(self, query: str, limit: int, cursor) -> tuple[list, float]:
        start = time.perf_counter()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000
        return rows, elapsed

    def setup(self, conn) -> None:
        TMP_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, conn) -> BenchmarkResult:
        matplotlib.use("Agg", force=True)
        limits = list(range(START, 0, -STEP))
        query_1 = self._get_query("query_1.sql")
        query_2 = self._get_query("query_2.sql")

        q1_times, q2_times = [], []
        q1_rows, q2_rows = [], []

        with conn.cursor() as cursor:
            for limit in limits:
                rows_1, t1 = self._measure(query_1, limit, cursor)
                rows_2, t2 = self._measure(query_2, limit, cursor)
                q1_times.append(t1)
                q2_times.append(t2)
                q1_rows.append(len(rows_1) if rows_1 else 0)
                q2_rows.append(len(rows_2) if rows_2 else 0)

        q1 = QueryResult(
            name=QUERY_1_NAME, query=query_1,
            times=q1_times, limits=limits, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name=QUERY_2_NAME, query=query_2,
            times=q2_times, limits=limits, rows_fetched=q2_rows,
        )

        comparison = self._build_comparison(q1, q2)
        plot = self._build_plot(q1, q2)

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2], comparison_table=comparison, plot_buffer=plot,
        )

    def _build_comparison(self, q1: QueryResult, q2: QueryResult) -> pd.DataFrame:
        rows = []
        for i, limit in enumerate(q1.limits):
            diff = q1.times[i] - q2.times[i]
            speedup = f"{q1.times[i] / q2.times[i]:.1f}x" if q2.times[i] > 0 else "N/A"
            rows.append({
                "limit": limit,
                "select_star": f"{q1.times[i]:.2f} ms",
                "select_columns": f"{q2.times[i]:.2f} ms",
                "speedup": speedup,
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1: QueryResult, q2: QueryResult) -> io.BytesIO:
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name)
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name)
        ax.set_title(self.title)
        ax.set_xlabel("LIMIT")
        ax.set_ylabel("Execution Time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
