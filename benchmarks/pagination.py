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
    CostCentre,
    QueryResult,
    Takeaway,
    format_ms,
    measure,
    ratio,
    speedup,
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

        m1, m2 = [], []
        with conn.cursor() as cur:
            for offset in offsets:
                m1.append(measure(cur, QUERY_OFFSET, (PAGE_SIZE, offset)))
                m2.append(measure(cur, QUERY_KEYSET, (offset, PAGE_SIZE)))

        q1 = QueryResult(
            name="OFFSET", query=QUERY_OFFSET, limits=offsets,
            times=[m.wall_ms for m in m1], rows_fetched=[m.rows_fetched for m in m1],
            server_times=[m.server_ms for m in m1],
        )
        q2 = QueryResult(
            name="Keyset (WHERE id >)", query=QUERY_KEYSET, limits=offsets,
            times=[m.wall_ms for m in m2], rows_fetched=[m.rows_fetched for m in m2],
            server_times=[m.server_ms for m in m2],
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
            takeaway=self._takeaway(q1, q2),
        )

    def _takeaway(self, q1: QueryResult, q2: QueryResult) -> Takeaway:
        last = -1
        page = q1.limits[last] // PAGE_SIZE + 1
        server = ratio(q1.server_times[last], q2.server_times[last])
        first_server = q1.server_times[0]
        deep_server = q1.server_times[last]

        points = [
            f"Every point returns one page of {PAGE_SIZE} rows, so the amount of data sent "
            "back is identical throughout — only the depth changes.",
            f"OFFSET grows with depth: {format_ms(first_server)} on page 1, "
            f"{format_ms(deep_server)} on page {page:,}.",
            f"Keyset does not: {format_ms(q2.server_times[0])} on page 1, "
            f"{format_ms(q2.server_times[last])} on page {page:,}.",
        ]
        if server:
            points.append(
                f"At page {page:,} that is {server:.0f}x more database time for identical output."
            )

        return Takeaway(
            verdict=(
                f"By page {page:,}, OFFSET makes PostgreSQL do {server:.0f}x more work "
                f"to return the same {PAGE_SIZE} rows"
                if server else "OFFSET degrades with page depth while keyset stays flat"
            ),
            cost_centre=CostCentre.DATABASE,
            points=points,
            advice=(
                "Unlike SELECT *, this one really is the database's problem: OFFSET has to walk "
                "and discard every row it skips, so page 1,000 costs a thousand pages of work. "
                "Keyset pagination asks the index to jump straight to the last id you saw. "
                "Trading OFFSET for a WHERE id > ? is the fix — no amount of client tuning helps."
            ),
        )

    def _build_comparison(self, q1, q2):
        rows = []
        for i, offset in enumerate(q1.limits):
            rows.append({
                "offset": offset,
                "page": offset // PAGE_SIZE + 1,
                "rows": q1.rows_fetched[i],
                "offset (total)": format_ms(q1.times[i]),
                "offset (server)": format_ms(q1.server_times[i]),
                "keyset (total)": format_ms(q2.times[i]),
                "keyset (server)": format_ms(q2.server_times[i]),
                "speedup (server)": speedup(q1.server_times[i], q2.server_times[i]),
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
