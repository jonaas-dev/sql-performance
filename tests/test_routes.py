def test_landing_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"SQL Performance Benchmark" in response.data
    assert b"select_star" in response.data
    assert b"Generate" in response.data


def test_generate_without_a_database_shows_a_generic_error():
    """The old assertion was `has_error or has_results`, and "Generate" is the
    button label, so it held on every page — it could never fail."""
    from app import create_app
    from app.config import Config

    class UnreachableConfig(Config):
        def __init__(self):
            super().__init__()
            self.DB_HOST = "127.0.0.1"
            self.DB_PORT = 1  # nothing listens here

    client = create_app(UnreachableConfig).test_client()
    response = client.get("/generate")

    assert response.status_code == 200
    assert b"Benchmark execution failed" in response.data
    assert b"alert-danger" in response.data
    assert b"psycopg2" not in response.data, "internal errors must not leak"


def test_generate_with_benchmark_param(client):
    response = client.get("/generate?benchmark=select_star")
    assert response.status_code == 200
    assert b"SQL Performance Benchmark" in response.data


def test_generate_unknown_benchmark(client):
    response = client.get("/generate?benchmark=nonexistent")
    assert response.status_code == 200
    assert b"Unknown benchmark" in response.data


def test_history_page(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Benchmark History" in response.data


def test_view_result_not_found(client):
    response = client.get("/results/nonexistent")
    assert response.status_code == 200
    assert b"Result not found" in response.data
    assert b"alert-danger" in response.data


def test_view_result_found(client, monkeypatch, tmp_path):
    monkeypatch.setattr("app.history.RESULTS_DIR", tmp_path)
    import io

    import pandas as pd

    from app.history import save_result
    from benchmarks.base import BenchmarkResult, QueryResult

    q1 = QueryResult(name="Q1", query="SELECT 1", times=[1.0], limits=[100], rows_fetched=[100])
    comparison = pd.DataFrame({"limit": [100], "q1": ["1.00 ms"]})
    buf = io.BytesIO()
    buf.write(b"\x89PNG")
    buf.seek(0)
    result = BenchmarkResult(
        name="test", title="Test Result", description="A test",
        queries=[q1], comparison_table=comparison, plot_buffer=buf,
    )
    result_id = save_result(result, {"size": "small"})

    response = client.get(f"/results/{result_id}")
    assert response.status_code == 200
    assert b"Test Result" in response.data
