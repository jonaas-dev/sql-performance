import logging

from flask import Blueprint, render_template, request

from app.benchmark import run_benchmark, result_to_plot_data, list_benchmarks
from app.db import get_db_connection
from benchmarks import get as get_benchmark

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)

VALID_SIZES = {"small", "medium", "large"}


@bp.route("/")
def landing():
    benchmarks = list_benchmarks()
    return render_template(
        "results.html",
        plot_data=None,
        comparison_table=None,
        benchmarks=benchmarks,
        selected_benchmark=None,
        selected_size="medium",
    )


@bp.route("/generate")
def generate():
    benchmark_name = request.args.get("benchmark", "select_star")
    size = request.args.get("size", "medium")

    if size not in VALID_SIZES:
        size = "medium"

    if get_benchmark(benchmark_name) is None:
        benchmarks = list_benchmarks()
        return render_template(
            "results.html",
            plot_data=None,
            comparison_table=None,
            benchmarks=benchmarks,
            selected_benchmark=benchmark_name,
            selected_size=size,
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
            selected_size=size,
            error=str(e),
        )

    benchmarks = list_benchmarks()
    return render_template(
        "results.html",
        plot_data=result_to_plot_data(result),
        comparison_table=result.comparison_table,
        benchmarks=benchmarks,
        selected_benchmark=benchmark_name,
        selected_size=size,
        benchmark_title=result.title,
        benchmark_description=result.description,
        explain_plans=result.explain_plans or None,
    )
