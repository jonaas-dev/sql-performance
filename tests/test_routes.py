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
    assert b"connection refused" in response.data.lower() or b"alert-danger" in response.data


def test_generate_with_benchmark_param(client):
    response = client.get("/generate?benchmark=select_star")
    assert response.status_code == 200
    assert b"SQL Performance Benchmark" in response.data


def test_generate_unknown_benchmark(client):
    response = client.get("/generate?benchmark=nonexistent")
    assert response.status_code == 200
    assert b"Unknown benchmark" in response.data
