import io

import matplotlib

matplotlib.use("Agg")
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from benchmarks.base import (
    BenchmarkBase,
    BenchmarkNotApplicable,
    BenchmarkResult,
    QueryResult,
    measure,
    table_row_count,
)
from benchmarks.registry import register

DATA_POINTS = 10

QUERY_ALL_COLUMNS = "SELECT * FROM users LIMIT %s"
QUERY_THREE_COLUMNS = "SELECT id, name, email FROM users LIMIT %s"

LABEL_ALL_COLUMNS = "SELECT *"
LABEL_THREE_COLUMNS = "SELECT id, name, email"


@register
class SelectStarBenchmark(BenchmarkBase):
    name = "select_star"
    title = "SELECT * vs SELECT columns"
    description = "Demonstrates why SELECT * is slow and selecting specific columns is fast"
    required_tables = ["users"]

    def _limits(self, total: int) -> list[int]:
        """LIMITs must stay inside the table: a LIMIT above the row count
        returns the whole table every time and flattens the curve into noise."""
        step = total // DATA_POINTS
        if step < 1:
            raise BenchmarkNotApplicable(
                f"select_star needs at least {DATA_POINTS} rows, found {total}"
            )
        return [step * i for i in range(1, DATA_POINTS + 1)]

    def setup(self, conn) -> None:
        self.check_requirements(conn)

    def run(self, conn) -> BenchmarkResult:
        limits = self._limits(table_row_count(conn))

        q1_times, q2_times = [], []
        q1_rows, q2_rows = [], []

        with conn.cursor() as cursor:
            for limit in limits:
                rows_1, t1 = measure(cursor, QUERY_ALL_COLUMNS, (limit,))
                rows_2, t2 = measure(cursor, QUERY_THREE_COLUMNS, (limit,))
                q1_times.append(t1)
                q2_times.append(t2)
                q1_rows.append(rows_1)
                q2_rows.append(rows_2)

        q1 = QueryResult(
            name=LABEL_ALL_COLUMNS, query=QUERY_ALL_COLUMNS,
            times=q1_times, limits=limits, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name=LABEL_THREE_COLUMNS, query=QUERY_THREE_COLUMNS,
            times=q2_times, limits=limits, rows_fetched=q2_rows,
        )

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2],
            comparison_table=self._build_comparison(q1, q2),
            plot_buffer=self._build_plot(q1, q2),
        )

    def _build_comparison(self, q1: QueryResult, q2: QueryResult) -> pd.DataFrame:
        rows = []
        for i, limit in enumerate(q1.limits):
            speedup = f"{q1.times[i] / q2.times[i]:.1f}x" if q2.times[i] > 0 else "N/A"
            rows.append({
                "limit": limit,
                "rows_fetched": q1.rows_fetched[i],
                "select_star": f"{q1.times[i]:.2f} ms",
                "select_columns": f"{q2.times[i]:.2f} ms",
                "speedup": speedup,
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1: QueryResult, q2: QueryResult) -> io.BytesIO:
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name, color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name, color="#2ecc71")
        ax.set_title(f"{self.title} (median of {len(q1.limits)} points)")
        ax.set_xlabel("LIMIT (rows fetched)")
        ax.set_ylabel("Median execution time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
