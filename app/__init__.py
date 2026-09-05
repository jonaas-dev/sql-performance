import logging

from flask import Flask

from app.config import Config


def create_app(config_class=None):
    app = Flask(__name__)

    if config_class is None:
        config = Config()
    elif isinstance(config_class, type):
        config = config_class()
    else:
        config = config_class

    app.config['DB_HOST'] = config.DB_HOST
    app.config['DB_PORT'] = config.DB_PORT
    app.config['DB_USER'] = config.DB_USER
    app.config['DB_PASSWORD'] = config.DB_PASSWORD
    app.config['DB_NAME'] = config.DB_NAME
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['TESTING'] = getattr(config, 'TESTING', False)

    app._db_config = config

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    from app.routes import bp
    app.register_blueprint(bp)

    return app
