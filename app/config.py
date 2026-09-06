import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
QUERIES_DIR = BASE_DIR / 'queries'

QUERY_1_NAME = 'SELECT *'
QUERY_2_NAME = 'SELECT id, name, email'


class Config:
    def __init__(self):
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_USER = os.getenv('DB_USER', 'user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        self.DB_NAME = os.getenv('DB_NAME', 'test_db')
        self.DB_SEED_SIZE = os.getenv('DB_SEED_SIZE', 'medium')
        self.TESTING = False
