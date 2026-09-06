import base64
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.config import BASE_DIR
from benchmarks.base import BenchmarkResult

RESULTS_DIR = BASE_DIR / "results"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H-%M-%S"


def _unique_dir(dirname: str) -> Path:
    """Two runs within the same second would otherwise overwrite each other."""
    candidate = RESULTS_DIR / dirname
    suffix = 2
    while candidate.exists():
        candidate = RESULTS_DIR / f"{dirname}-{suffix}"
        suffix += 1
    return candidate


def _resolve(result_id: str) -> Path | None:
    """Reject anything that escapes RESULTS_DIR.

    `result_id` comes straight from the URL and is used to build a filesystem
    path, so it is validated rather than trusted.
    """
    if not result_id or "/" in result_id or "\\" in result_id or result_id.startswith("."):
        return None

    resolved = (RESULTS_DIR / result_id).resolve()
    if resolved.parent != RESULTS_DIR.resolve():
        return None
    return resolved


def save_result(result: BenchmarkResult, params: dict) -> str:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    result_dir = _unique_dir(f"{timestamp}_{result.name}")
    result_dir.mkdir(parents=True)

    metadata = {
        "benchmark": result.name,
        "title": result.title,
        "description": result.description,
        "timestamp": timestamp,
        "params": params,
        "queries": [
            {"name": q.name, "query": q.query, "limits": q.limits, "times": q.times,
             "rows_fetched": q.rows_fetched}
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

    return result_dir.name


def list_results(limit: int = 8, offset: int = 0) -> tuple[list[dict], int]:
    if not RESULTS_DIR.exists():
        return [], 0

    all_results = []
    for d in sorted(RESULTS_DIR.iterdir(), reverse=True):
        metadata_file = d / "metadata.json"
        if not d.is_dir() or not metadata_file.exists():
            continue
        try:
            meta = json.loads(metadata_file.read_text())
        except json.JSONDecodeError:
            continue
        meta["id"] = d.name
        all_results.append(meta)

    return all_results[offset : offset + limit], len(all_results)


def load_result(result_id: str) -> dict | None:
    result_dir = _resolve(result_id)
    if result_dir is None or not result_dir.is_dir():
        return None

    metadata_file = result_dir / "metadata.json"
    if not metadata_file.exists():
        return None

    try:
        meta = json.loads(metadata_file.read_text())
    except json.JSONDecodeError:
        return None
    meta["id"] = result_id

    plot_file = result_dir / "plot.png"
    if plot_file.exists():
        meta["plot_data"] = base64.b64encode(plot_file.read_bytes()).decode("utf-8")

    csv_file = result_dir / "comparison.csv"
    if csv_file.exists():
        meta["comparison_table"] = pd.read_csv(csv_file)

    explain_file = result_dir / "explain_plans.json"
    if explain_file.exists():
        meta["explain_plans"] = json.loads(explain_file.read_text())

    return meta
