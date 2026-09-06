import logging
import os

import matplotlib

matplotlib.use("Agg")

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

    app.config["DB_CONFIG"] = config
    app.config["TESTING"] = getattr(config, "TESTING", False)

    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    from app.routes import bp
    app.register_blueprint(bp)

    return app
