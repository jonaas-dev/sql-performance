import json
from datetime import datetime
from pathlib import Path

from benchmarks.base import BenchmarkResult
from app.config import BASE_DIR

RESULTS_DIR = BASE_DIR / "results"


def save_result(result: BenchmarkResult, params: dict) -> str:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    dirname = f"{timestamp}_{result.name}"
    result_dir = RESULTS_DIR / dirname
    result_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "benchmark": result.name,
        "title": result.title,
        "description": result.description,
        "timestamp": timestamp,
        "params": params,
        "queries": [
            {"name": q.name, "query": q.query, "limits": q.limits, "times": q.times}
            for q in result.queries
        ],
    }
    (result_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

    (result_dir / "plot.png").write_bytes(result.plot_buffer.getvalue())

    result.comparison_table.to_csv(result_dir / "comparison.csv", index=False)

    if result.explain_plans:
        (result_dir / "explain_plans.json").write_text(
            json.dumps(result.explain_plans, indent=2)
        )

    return dirname


def list_results(limit: int = 8, offset: int = 0) -> tuple[list[dict], int]:
    if not RESULTS_DIR.exists():
        return [], 0

    all_results = []
    for d in sorted(RESULTS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        metadata_file = d / "metadata.json"
        if metadata_file.exists():
            meta = json.loads(metadata_file.read_text())
            meta["id"] = d.name
            all_results.append(meta)

    total = len(all_results)
    return all_results[offset : offset + limit], total


def load_result(result_id: str) -> dict | None:
    result_dir = RESULTS_DIR / result_id
    if not result_dir.exists():
        return None

    metadata_file = result_dir / "metadata.json"
    if not metadata_file.exists():
        return None

    meta = json.loads(metadata_file.read_text())
    meta["id"] = result_id

    plot_file = result_dir / "plot.png"
    if plot_file.exists():
        import base64
        meta["plot_data"] = base64.b64encode(plot_file.read_bytes()).decode("utf-8")

    csv_file = result_dir / "comparison.csv"
    if csv_file.exists():
        import pandas as pd
        meta["comparison_table"] = pd.read_csv(csv_file)

    explain_file = result_dir / "explain_plans.json"
    if explain_file.exists():
        meta["explain_plans"] = json.loads(explain_file.read_text())

    return meta
