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
    format_ms,
    measure,
    plot_server_series,
    speedup,
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

        m1, m2 = [], []
        with conn.cursor() as cursor:
            for limit in limits:
                m1.append(measure(cursor, QUERY_ALL_COLUMNS, (limit,)))
                m2.append(measure(cursor, QUERY_THREE_COLUMNS, (limit,)))

        q1 = QueryResult(
            name=LABEL_ALL_COLUMNS, query=QUERY_ALL_COLUMNS, limits=limits,
            times=[m.wall_ms for m in m1], rows_fetched=[m.rows_fetched for m in m1],
            server_times=[m.server_ms for m in m1],
        )
        q2 = QueryResult(
            name=LABEL_THREE_COLUMNS, query=QUERY_THREE_COLUMNS, limits=limits,
            times=[m.wall_ms for m in m2], rows_fetched=[m.rows_fetched for m in m2],
            server_times=[m.server_ms for m in m2],
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
            rows.append({
                "limit": limit,
                "rows": q1.rows_fetched[i],
                "select_star (total)": format_ms(q1.times[i]),
                "select_star (server)": format_ms(q1.server_times[i]),
                "3 cols (total)": format_ms(q2.times[i]),
                "3 cols (server)": format_ms(q2.server_times[i]),
                "speedup (total)": speedup(q1.times[i], q2.times[i]),
                "speedup (server)": speedup(q1.server_times[i], q2.server_times[i]),
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1: QueryResult, q2: QueryResult) -> io.BytesIO:
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=f"{q1.name} — total", color="#e74c3c")
        ax.plot(q2.limits, q2.times, marker="s", label=f"{q2.name} — total", color="#2ecc71")
        plot_server_series(ax, q1, "#e74c3c")
        plot_server_series(ax, q2, "#2ecc71")
        ax.set_title(f"{self.title} — solid: total, dashed: PostgreSQL only")
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
