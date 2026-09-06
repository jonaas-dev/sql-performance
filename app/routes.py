import logging

from flask import Blueprint, current_app, render_template, request

from app.benchmark import list_benchmarks, result_to_plot_data, run_benchmark
from app.db import get_db_connection
from app.history import list_results, load_result, save_result
from benchmarks import get as get_benchmark
from benchmarks.base import BenchmarkNotApplicable
from sql.seed import SIZES, resolve_size, seed

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)


def _results_page(**kwargs):
    defaults = {
        "plot_data": None,
        "comparison_table": None,
        "benchmarks": list_benchmarks(),
        "selected_benchmark": None,
        "selected_size": "medium",
        "sizes": SIZES,
    }
    return render_template("results.html", **{**defaults, **kwargs})


@bp.route("/")
def landing():
    return _results_page()


@bp.route("/generate")
def generate():
    benchmark_name = request.args.get("benchmark", "select_star")
    size = resolve_size(request.args.get("size"))

    if get_benchmark(benchmark_name) is None:
        return _results_page(
            selected_benchmark=benchmark_name,
            selected_size=size,
            error=f"Unknown benchmark: {benchmark_name}",
        )

    try:
        conn = get_db_connection(current_app.config["DB_CONFIG"])
        try:
            seed(conn, size)
            result = run_benchmark(conn, benchmark_name)
        finally:
            conn.close()
    except BenchmarkNotApplicable as e:
        logger.warning("Benchmark not applicable: %s", e)
        return _results_page(
            selected_benchmark=benchmark_name, selected_size=size, error=str(e)
        )
    except Exception as e:
        logger.exception("Benchmark failed: %s", e)
        return _results_page(
            selected_benchmark=benchmark_name,
            selected_size=size,
            error="Benchmark execution failed. Please check your configuration and try again.",
        )

    result_id = save_result(result, {"benchmark": benchmark_name, "size": size})

    return _results_page(
        plot_data=result_to_plot_data(result),
        comparison_table=result.comparison_table,
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
    results, total = list_results(limit=per_page, offset=(page - 1) * per_page)
    return render_template(
        "history.html",
        results=results,
        page=page,
        total_pages=max(1, -(-total // per_page)),
        total=total,
    )


@bp.route("/results/<result_id>")
def view_result(result_id):
    data = load_result(result_id)
    if data is None:
        results, total = list_results()
        return render_template(
            "history.html",
            results=results,
            error="Result not found",
            page=1,
            total_pages=1,
            total=total,
        )

    return render_template(
        "view_result.html",
        result=data,
        plot_data=data.get("plot_data"),
        comparison_table=data.get("comparison_table"),
        explain_plans=data.get("explain_plans"),
    )
