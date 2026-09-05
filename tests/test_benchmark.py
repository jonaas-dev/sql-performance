import io
import pandas as pd
from unittest.mock import MagicMock, patch
from app.benchmark import (
    measure_query_time,
    get_query_from_file,
    save_to_csv,
    generate_comparison_table,
    generate_plot_from_csv,
)
from app.config import QUERIES_DIR, TMP_DIR


def test_measure_query_time_success():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(1,)]
    mock_cursor.execute.return_value = None

    rows, exec_time = measure_query_time('SELECT 1', 100, mock_cursor)

    assert rows == [(1,)]
    assert isinstance(exec_time, float)
    assert exec_time >= 0


def test_measure_query_time_error():
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Exception('DB error')

    rows, error = measure_query_time('BAD SQL', 100, mock_cursor)

    assert rows is None
    assert error == 'DB error'


def test_get_query_from_file():
    query = get_query_from_file(str(QUERIES_DIR / 'query_1.sql'))
    assert 'SELECT' in query
    assert 'LIMIT' in query


def test_get_query_from_file_missing():
    try:
        get_query_from_file('/nonexistent/file.sql')
        assert False, 'Should have raised'
    except FileNotFoundError:
        pass


def test_save_to_csv(tmp_path):
    data = [{'limit': 100, 'time': 1.5}, {'limit': 200, 'time': 2.3}]
    filename = str(tmp_path / 'test.csv')

    df = save_to_csv(data, filename)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['limit', 'time']


def test_generate_comparison_table():
    q1 = [
        {'limit': 1000, 'time': 10.0, 'rows': []},
        {'limit': 500, 'time': 5.0, 'rows': []},
    ]
    q2 = [
        {'limit': 1000, 'time': 2.0, 'rows': []},
        {'limit': 500, 'time': 1.0, 'rows': []},
    ]

    table = generate_comparison_table(q1, q2)

    assert isinstance(table, pd.DataFrame)
    assert len(table) == 2
    assert '10.00 ms' in table.iloc[0]['query_1_time']
    assert '8.00 ms' in table.iloc[0]['time_difference']


def test_generate_plot_from_csv(tmp_path):
    df1 = pd.DataFrame({'limit': [100, 200], 'time': [1.0, 2.0]})
    df2 = pd.DataFrame({'limit': [100, 200], 'time': [0.5, 1.0]})

    file1 = str(tmp_path / 'q1.csv')
    file2 = str(tmp_path / 'q2.csv')
    df1.to_csv(file1, index=False)
    df2.to_csv(file2, index=False)

    buf = generate_plot_from_csv(file1, file2)

    assert isinstance(buf, io.BytesIO)
    assert len(buf.getvalue()) > 0
    assert buf.getvalue()[:4] == b'\x89PNG'
