import importlib
import pkgutil
from pathlib import Path

from benchmarks.base import BenchmarkBase

_registry: dict[str, BenchmarkBase] = {}


def _discover():
    package_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
        if module_name.startswith("_") or module_name in ("base", "registry"):
            continue
        importlib.import_module(f"benchmarks.{module_name}")


def register(benchmark_cls: type[BenchmarkBase]) -> type[BenchmarkBase]:
    instance = benchmark_cls()
    _registry[instance.name] = instance
    return benchmark_cls


def get(name: str) -> BenchmarkBase | None:
    if not _registry:
        _discover()
    return _registry.get(name)


def all() -> list[BenchmarkBase]:
    if not _registry:
        _discover()
    return list(_registry.values())


def default() -> BenchmarkBase:
    if not _registry:
        _discover()
    if "select_star" in _registry:
        return _registry["select_star"]
    return list(_registry.values())[0]
