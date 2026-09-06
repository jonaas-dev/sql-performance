from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd


@dataclass
class QueryResult:
    name: str
    query: str
    times: list[float]
    limits: list[int]
    rows_fetched: list[int]


@dataclass
class BenchmarkResult:
    name: str
    title: str
    description: str
    queries: list[QueryResult]
    comparison_table: pd.DataFrame
    plot_buffer: BytesIO
    explain_plans: dict[str, str] = field(default_factory=dict)


class BenchmarkBase(ABC):
    name: str = ""
    title: str = ""
    description: str = ""
    required_tables: list[str] = []

    @abstractmethod
    def setup(self, conn) -> None:
        pass

    @abstractmethod
    def run(self, conn) -> BenchmarkResult:
        pass

    def teardown(self, conn) -> None:
        pass
