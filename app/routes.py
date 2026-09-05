import logging

from flask import Blueprint, render_template

from app.benchmark import run_benchmark
from app.db import get_db_connection

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


@bp.route('/')
def landing():
    return render_template('results.html', plot_data=None, comparison_table=None)


@bp.route('/generate')
def generate():
    try:
        conn = get_db_connection()
        try:
            plot_data, comparison_table = run_benchmark(conn)
        finally:
            conn.close()
    except Exception as e:
        logger.exception("Benchmark failed")
        return render_template('results.html', plot_data=None, comparison_table=None, error=str(e))

    return render_template('results.html', plot_data=plot_data, comparison_table=comparison_table)
