import re
import statistics
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from io import BytesIO

import pandas as pd

REPETITIONS = 5

_EXECUTION_TIME = re.compile(r"Execution Time:\s*([\d.]+)\s*ms")


@dataclass
class Measurement:
    """One data point, split into where the time actually goes.

    `wall_ms` is what an application feels: planning, execution, transfer and
    the driver turning bytes into Python objects. `server_ms` is what
    PostgreSQL reports for itself. The gap between them is usually most of the
    total, and pretending otherwise is how a client-side cost gets presented
    as a database result.
    """

    rows_fetched: int
    wall_ms: float
    server_ms: float | None

    @property
    def client_ms(self) -> float | None:
        if self.server_ms is None:
            return None
        return max(0.0, self.wall_ms - self.server_ms)

    @property
    def client_share(self) -> float | None:
        """Fraction of wall time spent outside PostgreSQL."""
        if self.server_ms is None or self.wall_ms <= 0:
            return None
        return max(0.0, (self.wall_ms - self.server_ms) / self.wall_ms)


class CostCentre(Enum):
    """Who actually pays for a slow query.

    Keeping these apart is the single most useful thing this tool does: a cost
    paid in the driver is fixed by asking for less data, while a cost paid in
    PostgreSQL is fixed by changing the query or the indexes. Optimising the
    wrong one wastes weeks.
    """

    DATABASE = (
        "PostgreSQL",
        "PostgreSQL itself does the extra work — more rows scanned, a worse plan. "
        "Fix it with indexes or a different query shape.",
    )
    CLIENT = (
        "the client",
        "PostgreSQL is barely involved. The time goes to transferring rows and to the "
        "driver turning bytes into objects, so the bill lands in your API process, not "
        "your database. Fix it by asking for less data.",
    )
    TRANSFER = (
        "the result set",
        "Both sides are doing reasonable work; there is simply more data crossing the "
        "wire than the question required. Fix it by returning fewer rows or columns.",
    )

    def __init__(self, label, description):
        self.label = label
        self.description = description


@dataclass
class Takeaway:
    """The conclusion a benchmark reached, derived from the run it just did.

    Built from measured values rather than written by hand, so it cannot drift
    away from the chart above it.
    """

    verdict: str
    cost_centre: CostCentre
    points: list[str]
    #: What to do about it.
    advice: str = ""

    def __post_init__(self):
        if not self.verdict.strip():
            raise ValueError("a takeaway needs a verdict")
        if not self.points:
            raise ValueError("a takeaway needs evidence; a conclusion without it is an opinion")


@dataclass
class QueryResult:
    name: str
    query: str
    times: list[float]
    #: x-axis values for this benchmark — a LIMIT, an OFFSET or a filter value
    #: depending on what the benchmark varies. Same length as `times`.
    limits: list
    rows_fetched: list[int]
    #: PostgreSQL's own Execution Time per data point, None where unavailable.
    server_times: list[float | None] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    name: str
    title: str
    description: str
    queries: list[QueryResult]
    comparison_table: pd.DataFrame
    plot_buffer: BytesIO
    explain_plans: dict[str, str] = field(default_factory=dict)
    takeaway: "Takeaway | None" = None


def server_execution_ms(cursor, query, params=None) -> float | None:
    """PostgreSQL's own Execution Time, excluding transfer to the client.

    TIMING OFF keeps the per-node instrumentation overhead out of the total.
    """
    cursor.execute("EXPLAIN (ANALYZE, TIMING OFF) " + query, params)
    for row in cursor.fetchall():
        match = _EXECUTION_TIME.search(row[0])
        if match:
            return float(match.group(1))
    return None


def measure(
    cursor, query, params=None, repetitions=REPETITIONS, clock=time.perf_counter
) -> Measurement:
    """Time a query as the median of `repetitions` runs after one warm-up.

    The warm-up matters more than the repetitions: without it whichever query
    runs first pays for the cold cache, which systematically favours whatever
    the benchmark runs second.
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()

    timings = []
    for _ in range(repetitions):
        start = clock()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        timings.append((clock() - start) * 1000)

    return Measurement(
        rows_fetched=len(rows),
        wall_ms=statistics.median(timings),
        server_ms=server_execution_ms(cursor, query, params),
    )


def table_row_count(conn, table: str = "users") -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table}")
        return cur.fetchone()[0]


def format_ms(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f} ms"


def speedup(slow: float | None, fast: float | None) -> str:
    if slow is None or not fast:
        return "n/a"
    return f"{slow / fast:.1f}x"


def ratio(slow: float | None, fast: float | None) -> float | None:
    if slow is None or fast is None or fast <= 0:
        return None
    return slow / fast


def percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.0f}%"


def plot_server_series(ax, query, color):
    """Dashed companion line showing PostgreSQL's own time.

    The gap to the solid line is the client: for a wide SELECT * it is most of
    the chart, which is the point.
    """
    if not query.server_times or any(t is None for t in query.server_times):
        return
    ax.plot(
        query.limits, query.server_times, linestyle="--", linewidth=1.2,
        marker=".", color=color, alpha=0.75, label=f"{query.name} — server",
    )


class BenchmarkNotApplicable(RuntimeError):
    """Raised when the current dataset is too small for the benchmark to mean anything."""


class BenchmarkBase(ABC):
    name: str = ""
    title: str = ""
    description: str = ""
    required_tables: list[str] = []

    def check_requirements(self, conn) -> None:
        """Fail loudly before measuring if a required table is missing."""
        for table in self.required_tables:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass(%s)", (table,))
                if cur.fetchone()[0] is None:
                    raise BenchmarkNotApplicable(
                        f"{self.name} requires a '{table}' table that does not exist"
                    )

    @abstractmethod
    def setup(self, conn) -> None:
        pass

    @abstractmethod
    def run(self, conn) -> BenchmarkResult:
        pass

    def teardown(self, conn) -> None:
        pass
