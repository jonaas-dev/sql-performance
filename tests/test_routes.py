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
