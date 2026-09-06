"""Parametrized seeder for the benchmark dataset.

Set-based on purpose: a row-by-row loop for the `large` dataset takes minutes,
which is unusable from a web request. `INSERT ... SELECT generate_series` keeps
even 1M rows in the seconds range.
"""
import logging
import os

logger = logging.getLogger(__name__)

FIRST_NAMES = [
    "John", "Jane", "Alice", "Bob", "Charlie", "Emily", "Daniel",
    "Sophia", "Liam", "Olivia", "Emma", "Noah", "Ava", "Ethan",
]
LAST_NAMES = [
    "Doe", "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Martinez", "Davis", "Miller", "Wilson", "Moore",
]
CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
]
COUNTRIES = [
    "USA", "Canada", "UK", "Germany", "France",
    "Spain", "Italy", "Australia", "India", "Brazil",
]

SIZES = {"small": 10_000, "medium": 100_000, "large": 1_000_000}
DEFAULT_SIZE = "medium"
LOCK_TIMEOUT = "5s"

# floor() and not a bare ::INT cast: casting a float to INT in PostgreSQL
# *rounds*, so `(random() * 10)::INT + 1` yields 11 on a 10-element array and
# silently produces NULLs for ~5% of the rows.
_INSERT = """
WITH arrays AS (
    SELECT %(first_names)s::TEXT[] AS first_names,
           %(last_names)s::TEXT[]  AS last_names,
           %(cities)s::TEXT[]      AS cities,
           %(countries)s::TEXT[]   AS countries
)
INSERT INTO users (name, surname, email, address, city, country,
                   postal_code, phone, age, bio)
SELECT
    a.first_names[1 + floor(random() * array_length(a.first_names, 1))::INT],
    a.last_names[1 + floor(random() * array_length(a.last_names, 1))::INT],
    'user' || g.i || '@example.com',
    'Street ' || (1 + floor(random() * 100)::INT) || ', Apt ' || (1 + floor(random() * 50)::INT),
    a.cities[1 + floor(random() * array_length(a.cities, 1))::INT],
    a.countries[1 + floor(random() * array_length(a.countries, 1))::INT],
    lpad((floor(random() * 90000)::INT + 10000)::TEXT, 5, '0'),
    '+1-' || lpad((floor(random() * 900)::INT + 100)::TEXT, 3, '0')
        || '-' || lpad((floor(random() * 900000)::INT + 100000)::TEXT, 6, '0'),
    18 + floor(random() * 61)::INT,
    'Bio for user ' || g.i
FROM generate_series(1, %(n)s) AS g(i), arrays a
"""


def row_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM users")
        return cur.fetchone()[0]


def resolve_size(size: str | None) -> str:
    return size if size in SIZES else DEFAULT_SIZE


def seed(conn, size: str = DEFAULT_SIZE) -> int:
    """Make the users table hold exactly the number of rows for `size`.

    Idempotent on the exact count so switching size in the UI actually reseeds,
    including downwards.
    """
    n = SIZES[resolve_size(size)]

    if row_count(conn) == n:
        logger.info("Dataset already at %s rows, skipping seed.", n)
        return n

    with conn.cursor() as cur:
        # TRUNCATE needs ACCESS EXCLUSIVE. Without a server-side timeout a
        # concurrent reader blocks it forever, and a client-side timeout cannot
        # interrupt libpq waiting on the socket — it would hang the worker.
        cur.execute("SET LOCAL lock_timeout = %s", (LOCK_TIMEOUT,))
        cur.execute("TRUNCATE users RESTART IDENTITY CASCADE")
        cur.execute(
            _INSERT,
            {
                "first_names": FIRST_NAMES,
                "last_names": LAST_NAMES,
                "cities": CITIES,
                "countries": COUNTRIES,
                "n": n,
            },
        )
        cur.execute("ANALYZE users")
    conn.commit()

    logger.info("Seeded %s rows into users table.", n)
    return n


if __name__ == "__main__":
    import psycopg2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "test_db"),
    )
    seed(connection, os.getenv("DB_SEED_SIZE", DEFAULT_SIZE))
    connection.close()
