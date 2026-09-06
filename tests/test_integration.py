"""Integration tests against a real PostgreSQL instance.

Skipped automatically when no database is reachable, so the unit suite still
runs offline. CI always provides one, so these gates are never silently skipped
there.
"""
import os

import pytest

from benchmarks import all as all_benchmarks
from benchmarks.registry import get
from sql.seed import SIZES, row_count, seed


def _connect():
    import psycopg2

    return psycopg2.connect(
        host=os.getenv("TEST_DB_HOST", "localhost"),
        port=int(os.getenv("TEST_DB_PORT", "5432")),
        user=os.getenv("TEST_DB_USER", "user"),
        password=os.getenv("TEST_DB_PASSWORD", "password"),
        database=os.getenv("TEST_DB_NAME", "test_db"),
    )


@pytest.fixture(scope="module")
def conn():
    try:
        connection = _connect()
    except Exception as exc:
        pytest.skip(f"no PostgreSQL available: {exc}")
    seed(connection, "small")
    yield connection
    connection.close()


def test_seed_creates_exactly_the_requested_number_of_rows(conn):
    seed(conn, "small")
    assert row_count(conn) == SIZES["small"]


def test_seed_leaves_no_null_values_in_generated_columns(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*) FROM users "
            "WHERE name IS NULL OR surname IS NULL OR address IS NULL "
            "OR city IS NULL OR country IS NULL"
        )
        assert cur.fetchone()[0] == 0


@pytest.mark.parametrize("name", [bm.name for bm in all_benchmarks()])
def test_every_benchmark_measures_a_non_empty_result_set(conn, name):
    """A benchmark that fetches zero rows is measuring nothing."""
    bm = get(name)
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    for query in result.queries:
        assert all(r > 0 for r in query.rows_fetched), (
            f"{name}/{query.name} fetched no rows: {query.rows_fetched}"
        )


def test_select_star_derives_its_limits_from_the_real_row_count(conn):
    """A LIMIT above the row count makes every data point identical."""
    total = row_count(conn)
    bm = get("select_star")
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    for query in result.queries:
        assert max(query.limits) <= total
        assert len(set(query.rows_fetched)) > 1, (
            f"every LIMIT returned the same {query.rows_fetched[0]} rows"
        )


def test_index_usage_reports_two_different_query_plans(conn):
    """The 'no index' plan must be captured before the index exists."""
    bm = get("index_usage")
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    plans = result.explain_plans
    no_index = next(v for k, v in plans.items() if "no index" in k.lower())
    with_index = next(v for k, v in plans.items() if "no index" not in k.lower())

    assert "Seq Scan" in no_index
    assert "Index" in with_index
    assert no_index != with_index


def test_pagination_varies_the_offset_not_the_page_size(conn):
    """The thesis is that OFFSET degrades with page *number*."""
    bm = get("pagination")
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    offsets = result.queries[0].limits
    assert len(set(offsets)) > 1, "offset must vary across data points"
    assert max(offsets) < row_count(conn)


def test_join_benchmark_leaves_a_pre_existing_orders_table_untouched(conn):
    """The tool must never drop a table it did not create."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS orders")
        cur.execute("CREATE TABLE orders (id SERIAL PRIMARY KEY, note TEXT)")
        cur.execute("INSERT INTO orders (note) VALUES ('user data')")
        conn.commit()

    bm = get("join_vs_subquery")
    bm.setup(conn)
    try:
        bm.run(conn)
    finally:
        bm.teardown(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT note FROM orders")
        assert cur.fetchall() == [("user data",)]
        cur.execute("DROP TABLE orders")
        conn.commit()


def test_generate_route_seeds_the_requested_dataset_size(conn):
    """The size selector must change the data, not just the label."""
    from app import create_app
    from app.config import Config

    class RouteConfig(Config):
        def __init__(self):
            super().__init__()
            self.DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
            self.DB_PORT = int(os.getenv("TEST_DB_PORT", "5432"))
            self.DB_USER = os.getenv("TEST_DB_USER", "user")
            self.DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "password")
            self.DB_NAME = os.getenv("TEST_DB_NAME", "test_db")

    seed(conn, "medium")
    assert row_count(conn) == SIZES["medium"]
    conn.commit()  # release ACCESS SHARE so the route's TRUNCATE can proceed

    client = create_app(RouteConfig).test_client()
    response = client.get("/generate?benchmark=select_star&size=small")

    assert response.status_code == 200
    assert row_count(conn) == SIZES["small"]


def test_seed_fails_fast_instead_of_hanging_on_a_locked_table(conn):
    """A blocked TRUNCATE would otherwise hang a gunicorn worker forever."""
    import psycopg2

    seed(conn, "small")
    conn.commit()

    blocker = _connect()
    with blocker.cursor() as cur:
        cur.execute("SELECT count(*) FROM users")  # holds ACCESS SHARE
    try:
        other = _connect()
        with pytest.raises(psycopg2.errors.LockNotAvailable):
            seed(other, "medium")
        other.close()
    finally:
        blocker.close()


def test_join_benchmark_data_is_one_to_many(conn):
    """With one order per user, JOIN never fans out and the three patterns
    collapse to the same plan — the benchmark would compare nothing."""
    bm = get("join_vs_subquery")
    bm.setup(conn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT max(c) FROM ("
                "  SELECT user_id, count(*) c FROM sqlperf_orders GROUP BY user_id"
                ") t"
            )
            assert cur.fetchone()[0] > 1, "orders must be 1:N for the comparison to mean anything"

        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    join, in_subquery = result.queries[0], result.queries[1]
    assert any(j > i for j, i in zip(join.rows_fetched, in_subquery.rows_fetched, strict=True)), (
        "JOIN must return more rows than IN/EXISTS somewhere, otherwise there is no fan-out"
    )


def test_every_benchmark_reports_server_side_timings(conn):
    """Wall time is mostly client deserialisation; without the server number
    a client-side cost reads as a database result."""
    for name in [bm.name for bm in all_benchmarks()]:
        bm = get(name)
        bm.setup(conn)
        try:
            result = bm.run(conn)
        finally:
            bm.teardown(conn)
        for query in result.queries:
            assert len(query.server_times) == len(query.times)
            assert all(t is not None for t in query.server_times), f"{name}/{query.name}"


@pytest.mark.parametrize("name", [bm.name for bm in all_benchmarks()])
def test_every_benchmark_states_a_conclusion(conn, name):
    """The point of the tool is the lesson, not the chart."""
    bm = get(name)
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    takeaway = result.takeaway
    assert takeaway is not None, f"{name} produced numbers but no conclusion"
    assert takeaway.verdict.strip()
    assert takeaway.points, "a conclusion with no evidence is an opinion"
    assert takeaway.cost_centre is not None


def test_select_star_blames_the_client_not_the_database(conn):
    """The whole lesson: SELECT * is not a database problem."""
    from benchmarks.base import CostCentre

    bm = get("select_star")
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    assert result.takeaway.cost_centre is CostCentre.CLIENT


def test_pagination_blames_the_database(conn):
    """Unlike SELECT *, a deep OFFSET really is PostgreSQL doing extra work."""
    from benchmarks.base import CostCentre

    bm = get("pagination")
    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    assert result.takeaway.cost_centre is CostCentre.DATABASE
