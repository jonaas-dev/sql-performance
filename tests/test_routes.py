def test_landing_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"SQL Performance Benchmark" in response.data
    assert b"select_star" in response.data
    assert b"Generate" in response.data


def test_generate_route_without_db(client):
    response = client.get("/generate")
    assert response.status_code == 200
    assert b"SQL Performance Benchmark" in response.data
    has_error = b"Database connection failed" in response.data or b"alert-danger" in response.data
    has_results = b"Results" in response.data or b"Generate" in response.data
    assert has_error or has_results


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
    from app.history import save_result
    from benchmarks.base import BenchmarkResult, QueryResult
    import io, pandas as pd

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
