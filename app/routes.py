import logging

from flask import Blueprint, render_template, request

from app.benchmark import run_benchmark, result_to_plot_data, list_benchmarks
from app.db import get_db_connection
from benchmarks import get as get_benchmark

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


@bp.route("/")
def landing():
    benchmarks = list_benchmarks()
    return render_template(
        "results.html",
        plot_data=None,
        comparison_table=None,
        benchmarks=benchmarks,
        selected_benchmark=None,
    )


@bp.route("/generate")
def generate():
    benchmark_name = request.args.get("benchmark", "select_star")

    if get_benchmark(benchmark_name) is None:
        benchmarks = list_benchmarks()
        return render_template(
            "results.html",
            plot_data=None,
            comparison_table=None,
            benchmarks=benchmarks,
            selected_benchmark=benchmark_name,
            error=f"Unknown benchmark: {benchmark_name}",
        )

    try:
        conn = get_db_connection()
        try:
            result = run_benchmark(conn, benchmark_name)
        finally:
            conn.close()
    except Exception as e:
        logger.exception("Benchmark failed")
        benchmarks = list_benchmarks()
        return render_template(
            "results.html",
            plot_data=None,
            comparison_table=None,
            benchmarks=benchmarks,
            selected_benchmark=benchmark_name,
            error=str(e),
        )

    benchmarks = list_benchmarks()
    return render_template(
        "results.html",
        plot_data=result_to_plot_data(result),
        comparison_table=result.comparison_table,
        benchmarks=benchmarks,
        selected_benchmark=benchmark_name,
        benchmark_title=result.title,
        benchmark_description=result.description,
        explain_plans=result.explain_plans or None,
    )
