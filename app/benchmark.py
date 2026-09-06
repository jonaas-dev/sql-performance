import base64

from benchmarks import all, default, get
from benchmarks.base import BenchmarkResult


def run_benchmark(conn, benchmark_name: str | None = None) -> BenchmarkResult:
    if benchmark_name:
        bm = get(benchmark_name)
        if bm is None:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")
    else:
        bm = default()

    bm.setup(conn)
    try:
        result = bm.run(conn)
    finally:
        bm.teardown(conn)

    return result


def result_to_plot_data(result: BenchmarkResult) -> str:
    return base64.b64encode(result.plot_buffer.getvalue()).decode("utf-8")


def list_benchmarks() -> list[dict]:
    return [
        {"name": bm.name, "title": bm.title, "description": bm.description}
        for bm in all()
    ]
