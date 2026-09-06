import io

import matplotlib

matplotlib.use("Agg")
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.benchmark import run_explain
from benchmarks.base import (
    BenchmarkBase,
    BenchmarkNotApplicable,
    BenchmarkResult,
    QueryResult,
    measure,
    table_row_count,
)
from benchmarks.registry import register

PAGE_SIZE = 100
DATA_POINTS = 6

QUERY_OFFSET = "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s"
QUERY_KEYSET = "SELECT * FROM users WHERE id > %s ORDER BY id LIMIT %s"


@register
class PaginationBenchmark(BenchmarkBase):
    name = "pagination"
    title = "OFFSET vs keyset pagination"
    description = "Demonstrates why OFFSET degrades at high page numbers and keyset stays constant"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        self.check_requirements(conn)

    def _offsets(self, total: int) -> list[int]:
        """The thesis is about page *number*, so the offset is what must vary.

        Every offset must leave a full page behind it, otherwise both queries
        return zero rows and the chart measures nothing.
        """
        usable = total - PAGE_SIZE
        if usable < DATA_POINTS:
            raise BenchmarkNotApplicable(
                f"pagination needs more than {PAGE_SIZE + DATA_POINTS} rows, found {total}"
            )
        step = usable // (DATA_POINTS - 1)
        return [step * i for i in range(DATA_POINTS)]

    def run(self, conn) -> BenchmarkResult:
        offsets = self._offsets(table_row_count(conn))

        q1_times, q1_rows = [], []
        q2_times, q2_rows = [], []

        with conn.cursor() as cur:
            for offset in offsets:
                rows, elapsed = measure(cur, QUERY_OFFSET, (PAGE_SIZE, offset))
                q1_times.append(elapsed)
                q1_rows.append(rows)

                rows, elapsed = measure(cur, QUERY_KEYSET, (offset, PAGE_SIZE))
                q2_times.append(elapsed)
                q2_rows.append(rows)

        q1 = QueryResult(
            name="OFFSET", query=QUERY_OFFSET,
            times=q1_times, limits=offsets, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name="Keyset (WHERE id >)", query=QUERY_KEYSET,
            times=q2_times, limits=offsets, rows_fetched=q2_rows,
        )

        deepest = offsets[-1]
        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2],
            comparison_table=self._build_comparison(q1, q2),
            plot_buffer=self._build_plot(q1, q2),
            explain_plans={
                q1.name: run_explain(conn, QUERY_OFFSET, (PAGE_SIZE, deepest)),
                q2.name: run_explain(conn, QUERY_KEYSET, (deepest, PAGE_SIZE)),
            },
        )

    def _build_comparison(self, q1, q2):
        rows = []
        for i, offset in enumerate(q1.limits):
            speedup = f"{q1.times[i] / q2.times[i]:.1f}x" if q2.times[i] > 0 else "N/A"
            rows.append({
                "offset": offset,
                "page": offset // PAGE_SIZE + 1,
                "rows_fetched": q1.rows_fetched[i],
                "offset_ms": f"{q1.times[i]:.2f} ms",
                "keyset_ms": f"{q2.times[i]:.2f} ms",
                "speedup": speedup,
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name, color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name, color="#2ecc71")
        ax.set_title(f"{self.title} (page size {PAGE_SIZE})")
        ax.set_xlabel("OFFSET (rows skipped)")
        ax.set_ylabel("Median execution time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
