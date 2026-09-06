import os

import matplotlib

matplotlib.use("Agg")

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        debug=os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes"),
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", "8000")),
    )
