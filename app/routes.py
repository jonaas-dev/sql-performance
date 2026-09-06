import logging

from flask import Blueprint, render_template, request

from app.benchmark import run_benchmark, result_to_plot_data, list_benchmarks
from app.db import get_db_connection
from app.history import save_result, list_results, load_result
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

    result_id = save_result(result, {"benchmark": benchmark_name, "size": size})

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
        result_id=result_id,
    )


@bp.route("/history")
def history():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 8
    offset = (page - 1) * per_page
    results, total = list_results(limit=per_page, offset=offset)
    total_pages = max(1, -(-total // per_page))
    return render_template(
        "history.html",
        results=results,
        page=page,
        total_pages=total_pages,
        total=total,
    )


@bp.route("/results/<result_id>")
def view_result(result_id):
    data = load_result(result_id)
    if data is None:
        return render_template("history.html", results=list_results(), error="Result not found")

    return render_template(
        "view_result.html",
        result=data,
        plot_data=data.get("plot_data"),
        comparison_table=data.get("comparison_table"),
        explain_plans=data.get("explain_plans"),
    )
