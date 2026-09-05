def test_landing_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Query Execution Results' in response.data
    assert b'Click "Generate"' in response.data


def test_generate_route_without_db(client):
    response = client.get('/generate')
    assert response.status_code == 200
    assert b'Query Execution Results' in response.data
