import psycopg2


def get_db_connection(config=None):
    if config is None:
        from app.config import Config
        config = Config()

    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )
