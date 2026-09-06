import logging
import random

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


def seed(conn, size: str = "medium"):
    n = SIZES.get(size, SIZES["medium"])

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        existing = cur.fetchone()[0]
        if existing >= n:
            logger.info("Database already has %s rows (>= %s), skipping seed.", existing, n)
            return

        cur.execute("TRUNCATE users RESTART IDENTITY CASCADE")

        for i in range(1, n + 1):
            cur.execute(
                """
                INSERT INTO users (name, surname, email, direction, city, country,
                                   postal_code, phone, age, bio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    random.choice(FIRST_NAMES),
                    random.choice(LAST_NAMES),
                    f"user{i}@example.com",
                    f"Street {random.randint(1, 100)}, Apt {random.randint(1, 50)}",
                    random.choice(CITIES),
                    random.choice(COUNTRIES),
                    f"{random.randint(10000, 99999)}",
                    f"+1-{random.randint(100, 999)}-{random.randint(100000, 999999)}",
                    random.randint(18, 78),
                    f"Bio for user {i}",
                ),
            )

            if i % 10_000 == 0:
                conn.commit()
                logger.info("Inserted %s/%s rows...", i, n)

        conn.commit()
        logger.info("Seeded %s rows into users table.", n)


if __name__ == "__main__":
    import os
    import psycopg2

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "test_db"),
    )
    size = os.getenv("DB_SEED_SIZE", "medium")
    seed(conn, size)
    conn.close()
