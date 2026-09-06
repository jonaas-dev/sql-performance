import io
import json

import pandas as pd

from app.history import list_results, load_result, save_result
from benchmarks.base import BenchmarkResult, QueryResult


def _make_result():
    q1 = QueryResult(name="Q1", query="SELECT 1", times=[1.0], limits=[100], rows_fetched=[100])
    q2 = QueryResult(name="Q2", query="SELECT 2", times=[0.5], limits=[100], rows_fetched=[100])
    comparison = pd.DataFrame({"limit": [100], "q1": ["1.00 ms"], "q2": ["0.50 ms"]})
    buf = io.BytesIO()
    buf.write(b"\x89PNG")
    buf.seek(0)
    return BenchmarkResult(
        name="test_benchmark", title="Test Benchmark", description="A test",
        queries=[q1, q2], comparison_table=comparison, plot_buffer=buf,
        explain_plans={"Q1": "Seq Scan on users"},
    )


def test_save_result(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    result = _make_result()
    result_id = save_result(result, {"size": "small"})

    assert (tmp_path / result_id).exists()
    assert (tmp_path / result_id / "metadata.json").exists()
    assert (tmp_path / result_id / "plot.png").exists()
    assert (tmp_path / result_id / "comparison.csv").exists()
    assert (tmp_path / result_id / "explain_plans.json").exists()

    meta = json.loads((tmp_path / result_id / "metadata.json").read_text())
    assert meta["benchmark"] == "test_benchmark"
    assert meta["params"]["size"] == "small"


def test_list_results(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    result = _make_result()
    save_result(result, {"size": "small"})

    results, total = list_results()
    assert total == 1
    assert len(results) == 1
    assert results[0]["benchmark"] == "test_benchmark"
    assert "id" in results[0]


def test_list_results_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    results, total = list_results()
    assert results == []
    assert total == 0


def test_load_result(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    result = _make_result()
    result_id = save_result(result, {"size": "small"})

    loaded = load_result(result_id)
    assert loaded is not None
    assert loaded["benchmark"] == "test_benchmark"
    assert "plot_data" in loaded
    assert "comparison_table" in loaded
    assert "explain_plans" in loaded


def test_load_result_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    loaded = load_result("nonexistent")
    assert loaded is None


def test_load_result_rejects_ids_that_escape_the_results_directory(tmp_path, monkeypatch):
    """result_id comes straight from the URL and is used to build a path."""
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    (tmp_path.parent / "metadata.json").write_text('{"secret": true}')

    assert load_result("..") is None
    assert load_result("../") is None
    assert load_result("/etc") is None


def test_save_result_does_not_overwrite_a_run_from_the_same_second(tmp_path, monkeypatch):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)

    first = save_result(_make_result(), {"size": "small"})
    second = save_result(_make_result(), {"size": "small"})

    assert first != second
    _, total = list_results()
    assert total == 2
