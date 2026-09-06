import io
import pandas as pd
from unittest.mock import MagicMock, patch
from benchmarks.base import BenchmarkResult, QueryResult
from benchmarks.registry import all, get, default, _registry
from benchmarks.select_star import SelectStarBenchmark
from benchmarks.index_usage import IndexUsageBenchmark
from benchmarks.join_vs_subquery import JoinVsSubqueryBenchmark
from benchmarks.pagination import PaginationBenchmark
from app.benchmark import run_benchmark, result_to_plot_data, list_benchmarks, run_explain
from app.config import QUERIES_DIR


def test_registry_discovery():
    benchmarks = all()
    assert len(benchmarks) >= 4
    names = [b.name for b in benchmarks]
    assert "select_star" in names
    assert "index_usage" in names
    assert "join_vs_subquery" in names
    assert "pagination" in names


def test_registry_get():
    bm = get("select_star")
    assert bm is not None
    assert isinstance(bm, SelectStarBenchmark)


def test_registry_get_index_usage():
    bm = get("index_usage")
    assert bm is not None
    assert isinstance(bm, IndexUsageBenchmark)


def test_registry_get_join_vs_subquery():
    bm = get("join_vs_subquery")
    assert bm is not None
    assert isinstance(bm, JoinVsSubqueryBenchmark)


def test_registry_get_pagination():
    bm = get("pagination")
    assert bm is not None
    assert isinstance(bm, PaginationBenchmark)


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


def test_index_usage_metadata():
    bm = IndexUsageBenchmark()
    assert bm.name == "index_usage"
    assert "index" in bm.title.lower()


def test_join_vs_subquery_metadata():
    bm = JoinVsSubqueryBenchmark()
    assert bm.name == "join_vs_subquery"
    assert "JOIN" in bm.title


def test_pagination_metadata():
    bm = PaginationBenchmark()
    assert bm.name == "pagination"
    assert "OFFSET" in bm.title


def test_list_benchmarks():
    result = list_benchmarks()
    assert isinstance(result, list)
    assert len(result) >= 4
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
    assert "10.00 ms" in table.iloc[0]["select_star"]
    assert "5.0x" in table.iloc[0]["speedup"]


def test_select_star_build_plot():
    bm = SelectStarBenchmark()
    q1 = QueryResult(name="Q1", query="SELECT 1", times=[1.0, 2.0], limits=[100, 200], rows_fetched=[100, 200])
    q2 = QueryResult(name="Q2", query="SELECT 2", times=[0.5, 1.0], limits=[100, 200], rows_fetched=[100, 200])

    buf = bm._build_plot(q1, q2)

    assert isinstance(buf, io.BytesIO)
    assert len(buf.getvalue()) > 0
    assert buf.getvalue()[:4] == b"\x89PNG"


def test_index_usage_build_plot():
    bm = IndexUsageBenchmark()
    q1 = QueryResult(name="No idx", query="SELECT 1", times=[10.0, 5.0], limits=[20, 30], rows_fetched=[1000, 500])
    q2 = QueryResult(name="Idx", query="SELECT 2", times=[2.0, 1.0], limits=[20, 30], rows_fetched=[1000, 500])

    buf = bm._build_plot(q1, q2)

    assert isinstance(buf, io.BytesIO)
    assert buf.getvalue()[:4] == b"\x89PNG"


def test_join_vs_subquery_build_plot():
    bm = JoinVsSubqueryBenchmark()
    q1 = QueryResult(name="JOIN", query="SELECT 1", times=[10.0], limits=[50], rows_fetched=[100])
    q2 = QueryResult(name="IN", query="SELECT 2", times=[8.0], limits=[50], rows_fetched=[100])
    q3 = QueryResult(name="EXISTS", query="SELECT 3", times=[9.0], limits=[50], rows_fetched=[100])

    buf = bm._build_plot(q1, q2, q3)

    assert isinstance(buf, io.BytesIO)
    assert buf.getvalue()[:4] == b"\x89PNG"


def test_pagination_build_plot():
    bm = PaginationBenchmark()
    q1 = QueryResult(name="OFFSET", query="SELECT 1", times=[10.0], limits=[100], rows_fetched=[100])
    q2 = QueryResult(name="Keyset", query="SELECT 2", times=[2.0], limits=[100], rows_fetched=[100])

    buf = bm._build_plot(q1, q2)

    assert isinstance(buf, io.BytesIO)
    assert buf.getvalue()[:4] == b"\x89PNG"


def test_run_explain():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchall.return_value = [
        ("Seq Scan on users  (cost=0.00..35482.00 rows=1000000 width=57)",),
        ("  Filter: (age > 30)",),
        ("Planning Time: 0.082 ms",),
        ("Execution Time: 150.123 ms",),
    ]

    plan = run_explain(mock_conn, "SELECT * FROM users WHERE age > %s", (30,))

    assert "Seq Scan on users" in plan
    assert "Execution Time" in plan
    assert mock_cursor.execute.called
