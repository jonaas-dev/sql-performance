import io
import pandas as pd
from unittest.mock import MagicMock, patch
from benchmarks.base import BenchmarkResult, QueryResult
from benchmarks.registry import all, get, default, _registry
from benchmarks.select_star import SelectStarBenchmark
from app.benchmark import run_benchmark, result_to_plot_data, list_benchmarks
from app.config import QUERIES_DIR


def test_registry_discovery():
    benchmarks = all()
    assert len(benchmarks) >= 1
    names = [b.name for b in benchmarks]
    assert "select_star" in names


def test_registry_get():
    bm = get("select_star")
    assert bm is not None
    assert isinstance(bm, SelectStarBenchmark)


def test_registry_get_unknown():
    bm = get("nonexistent")
    assert bm is None


def test_registry_default():
    bm = default()
    assert bm.name == "select_star"


def test_select_star_metadata():
    bm = SelectStarBenchmark()
    assert bm.name == "select_star"
    assert "SELECT" in bm.title
    assert len(bm.required_tables) > 0


def test_list_benchmarks():
    result = list_benchmarks()
    assert isinstance(result, list)
    assert len(result) >= 1
    assert "name" in result[0]
    assert "title" in result[0]
    assert "description" in result[0]


def test_result_to_plot_data():
    q1 = QueryResult(name="Q1", query="SELECT 1", times=[1.0, 2.0], limits=[100, 200], rows_fetched=[100, 200])
    q2 = QueryResult(name="Q2", query="SELECT 2", times=[0.5, 1.0], limits=[100, 200], rows_fetched=[100, 200])
    comparison = pd.DataFrame({"limit": [100, 200], "q1": ["1.00 ms", "2.00 ms"], "q2": ["0.50 ms", "1.00 ms"]})

    buf = io.BytesIO()
    buf.write(b"\x89PNG")
    buf.seek(0)

    result = BenchmarkResult(
        name="test", title="Test", description="Test benchmark",
        queries=[q1, q2], comparison_table=comparison, plot_buffer=buf,
    )

    plot_data = result_to_plot_data(result)
    assert isinstance(plot_data, str)
    assert len(plot_data) > 0


def test_select_star_build_comparison():
    bm = SelectStarBenchmark()
    q1 = QueryResult(name="Q1", query="SELECT 1", times=[10.0, 5.0], limits=[1000, 500], rows_fetched=[1000, 500])
    q2 = QueryResult(name="Q2", query="SELECT 2", times=[2.0, 1.0], limits=[1000, 500], rows_fetched=[1000, 500])

    table = bm._build_comparison(q1, q2)

    assert isinstance(table, pd.DataFrame)
    assert len(table) == 2
    assert "10.00 ms" in table.iloc[0]["query_1_time"]
    assert "8.00 ms" in table.iloc[0]["time_difference"]


def test_select_star_build_plot():
    bm = SelectStarBenchmark()
    q1 = QueryResult(name="Q1", query="SELECT 1", times=[1.0, 2.0], limits=[100, 200], rows_fetched=[100, 200])
    q2 = QueryResult(name="Q2", query="SELECT 2", times=[0.5, 1.0], limits=[100, 200], rows_fetched=[100, 200])

    buf = bm._build_plot(q1, q2)

    assert isinstance(buf, io.BytesIO)
    assert len(buf.getvalue()) > 0
    assert buf.getvalue()[:4] == b"\x89PNG"
