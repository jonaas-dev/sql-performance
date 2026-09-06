import os

import pytest

from app import create_app
from app.config import Config


class TestConfig(Config):
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.DB_HOST = os.getenv('TEST_DB_HOST', 'localhost')
        self.DB_PORT = int(os.getenv('TEST_DB_PORT', '5432'))
        self.DB_USER = os.getenv('TEST_DB_USER', 'user')
        self.DB_PASSWORD = os.getenv('TEST_DB_PASSWORD', 'password')
        self.DB_NAME = os.getenv('TEST_DB_NAME', 'test_db')


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()
