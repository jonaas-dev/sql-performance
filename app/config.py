import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
QUERIES_DIR = BASE_DIR / 'queries'
TMP_DIR = BASE_DIR / 'executions_tmp'

START = 1000000
STEP = 100000
QUERY_1_NAME = 'Query 1'
QUERY_2_NAME = 'Query 2'


class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'test_db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-prod')
