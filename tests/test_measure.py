import pytest

from benchmarks.base import REPETITIONS, measure


class FakeCursor:
    """Records every execute so we can assert on warm-up and repetitions."""

    def __init__(self, rows=3):
        self.executed = []
        self._rows = [(i,) for i in range(rows)]

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchall(self):
        return self._rows


def test_measure_discards_a_warmup_run_before_timing():
    cursor = FakeCursor()

    measure(cursor, "SELECT 1", repetitions=3)

    assert len(cursor.executed) == 4, "expected 1 warm-up + 3 timed runs"


def test_measure_returns_the_number_of_rows_fetched():
    cursor = FakeCursor(rows=7)

    rows, _ = measure(cursor, "SELECT 1")

    assert rows == 7


def test_measure_passes_params_through_on_every_run():
    cursor = FakeCursor()

    measure(cursor, "SELECT %s", params=(42,), repetitions=2)

    assert all(params == (42,) for _, params in cursor.executed)


def test_measure_reports_the_median_not_the_first_run():
    """One slow cold run must not drag the reported time; mean would give 20.8ms."""
    cursor = FakeCursor()
    # start/end pairs in seconds -> deltas of 100ms, 1ms, 1ms, 1ms, 1ms
    ticks = iter([0, 0.100, 0, 0.001, 0, 0.001, 0, 0.001, 0, 0.001])

    _, elapsed = measure(cursor, "SELECT 1", repetitions=5, clock=lambda: next(ticks))

    assert elapsed == pytest.approx(1.0)


def test_default_repetitions_is_more_than_one():
    assert REPETITIONS > 1
