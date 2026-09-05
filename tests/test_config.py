import os
from app.config import Config, BASE_DIR, QUERIES_DIR, TMP_DIR


def test_config_defaults():
    config = Config()
    assert config.DB_HOST == 'localhost'
    assert config.DB_PORT == 5432
    assert config.DB_USER == 'user'
    assert config.DB_PASSWORD == 'password'
    assert config.DB_NAME == 'test_db'


def test_config_from_env(monkeypatch):
    monkeypatch.setenv('DB_HOST', 'remote-host')
    monkeypatch.setenv('DB_PORT', '3306')
    monkeypatch.setenv('DB_USER', 'admin')
    monkeypatch.setenv('DB_PASSWORD', 'secret')
    monkeypatch.setenv('DB_NAME', 'mydb')

    config = Config()
    assert config.DB_HOST == 'remote-host'
    assert config.DB_PORT == 3306
    assert config.DB_USER == 'admin'
    assert config.DB_PASSWORD == 'secret'
    assert config.DB_NAME == 'mydb'


def test_config_port_cast(monkeypatch):
    monkeypatch.setenv('DB_PORT', '5433')
    config = Config()
    assert config.DB_PORT == 5433
    assert isinstance(config.DB_PORT, int)


def test_base_dir():
    assert BASE_DIR.exists()
    assert (BASE_DIR / 'app').exists()


def test_queries_dir():
    assert QUERIES_DIR.exists()
    assert (QUERIES_DIR / 'query_1.sql').exists()
    assert (QUERIES_DIR / 'query_2.sql').exists()
