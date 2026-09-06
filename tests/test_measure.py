import pytest

from benchmarks.base import REPETITIONS, measure

EXPLAIN_OUTPUT = [
    ("Seq Scan on users  (cost=0.00..3273.00 rows=100000 width=143)",),
    ("Planning Time: 0.041 ms",),
    ("Execution Time: 3.90 ms",),
]


class FakeCursor:
    """Records every execute so we can assert on warm-up and repetitions."""

    def __init__(self, rows=3):
        self.executed = []
        self._rows = [(i,) for i in range(rows)]

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        if self.executed and self.executed[-1][0].startswith("EXPLAIN"):
            return EXPLAIN_OUTPUT
        return self._rows

    @property
    def timed(self):
        return [q for q, _ in self.executed if not q.startswith("EXPLAIN")]


def test_measure_discards_a_warmup_run_before_timing():
    cursor = FakeCursor()

    measure(cursor, "SELECT 1", repetitions=3)

    assert len(cursor.timed) == 4, "expected 1 warm-up + 3 timed runs"


def test_measure_returns_the_number_of_rows_fetched():
    cursor = FakeCursor(rows=7)

    result = measure(cursor, "SELECT 1")

    assert result.rows_fetched == 7


def test_measure_passes_params_through_on_every_run():
    cursor = FakeCursor()

    measure(cursor, "SELECT %s", params=(42,), repetitions=2)

    assert all(params == (42,) for _, params in cursor.executed)


def test_measure_reports_the_median_wall_time_not_the_first_run():
    """One slow cold run must not drag the reported time; mean would give 20.8ms."""
    cursor = FakeCursor()
    ticks = iter([0, 0.100, 0, 0.001, 0, 0.001, 0, 0.001, 0, 0.001])

    result = measure(cursor, "SELECT 1", repetitions=5, clock=lambda: next(ticks))

    assert result.wall_ms == pytest.approx(1.0)


def test_measure_reports_the_server_execution_time_separately():
    """Wall time is dominated by client deserialisation; the planner's own cost
    only shows up in EXPLAIN."""
    cursor = FakeCursor()

    result = measure(cursor, "SELECT 1", repetitions=2)

    assert result.server_ms == pytest.approx(3.90)


def test_measure_asks_the_server_for_its_own_timing():
    cursor = FakeCursor()

    measure(cursor, "SELECT * FROM users", repetitions=2)

    explains = [q for q, _ in cursor.executed if q.startswith("EXPLAIN")]
    assert len(explains) == 1
    assert "ANALYZE" in explains[0]


def test_measure_survives_a_server_that_reports_no_execution_time():
    cursor = FakeCursor()
    cursor.fetchall = lambda: [("something unparseable",)]

    result = measure(cursor, "SELECT 1", repetitions=2)

    assert result.server_ms is None


def test_client_share_is_the_fraction_of_wall_time_spent_outside_postgres():
    cursor = FakeCursor()
    ticks = iter([0, 0.100, 0, 0.100, 0, 0.100])

    result = measure(cursor, "SELECT 1", repetitions=3, clock=lambda: next(ticks))

    # 100ms wall, 3.90ms server -> 96.1% of the time is not the database
    assert result.client_share == pytest.approx(0.961, abs=0.001)


def test_default_repetitions_is_more_than_one():
    assert REPETITIONS > 1
