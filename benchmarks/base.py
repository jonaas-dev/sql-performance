import statistics
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd

REPETITIONS = 5


@dataclass
class QueryResult:
    name: str
    query: str
    times: list[float]
    #: x-axis values for this benchmark — a LIMIT, an OFFSET or a filter value
    #: depending on what the benchmark varies. Same length as `times`.
    limits: list
    rows_fetched: list[int]


@dataclass
class BenchmarkResult:
    name: str
    title: str
    description: str
    queries: list[QueryResult]
    comparison_table: pd.DataFrame
    plot_buffer: BytesIO
    explain_plans: dict[str, str] = field(default_factory=dict)


def measure(cursor, query, params=None, repetitions=REPETITIONS, clock=time.perf_counter):
    """Time a query as the median of `repetitions` runs after one warm-up.

    The warm-up matters more than the repetitions: without it whichever query
    runs first pays for the cold cache, which systematically favours whatever
    the benchmark runs second.

    Returns (rows_fetched, median_milliseconds).
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()

    timings = []
    for _ in range(repetitions):
        start = clock()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        timings.append((clock() - start) * 1000)

    return len(rows), statistics.median(timings)


def table_row_count(conn, table: str = "users") -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {table}")
        return cur.fetchone()[0]


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
