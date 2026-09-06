import io

import matplotlib

matplotlib.use("Agg")
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.benchmark import run_explain
from benchmarks.base import (
    BenchmarkBase,
    BenchmarkResult,
    QueryResult,
    measure,
)
from benchmarks.registry import register

# Namespaced so the benchmark can never drop a table the user owns.
ORDERS = "sqlperf_orders"

QUERY_JOIN = f"""
    SELECT u.id, u.name, u.email, o.amount
    FROM users u
    INNER JOIN {ORDERS} o ON u.id = o.user_id
    WHERE o.amount > %s
"""
QUERY_SUBQUERY = f"""
    SELECT id, name, email
    FROM users
    WHERE id IN (SELECT user_id FROM {ORDERS} WHERE amount > %s)
"""
QUERY_EXISTS = f"""
    SELECT id, name, email
    FROM users u
    WHERE EXISTS (SELECT 1 FROM {ORDERS} o WHERE o.user_id = u.id AND o.amount > %s)
"""

THRESHOLDS = [50, 100, 200, 300, 400]
EXPLAIN_THRESHOLD = 100


@register
class JoinVsSubqueryBenchmark(BenchmarkBase):
    name = "join_vs_subquery"
    title = "JOIN vs subquery for filtering"
    description = "Compares JOIN, IN (subquery) and EXISTS for relational filtering"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        self.check_requirements(conn)
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {ORDERS}")
            cur.execute(f"""
                CREATE TABLE {ORDERS} (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    amount DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute(f"""
                INSERT INTO {ORDERS} (user_id, amount)
                SELECT id, (random() * 500)::DECIMAL(10,2)
                FROM users
                WHERE random() < 0.3
            """)
            cur.execute(f"CREATE INDEX ON {ORDERS}(user_id)")
            cur.execute(f"ANALYZE {ORDERS}")
            conn.commit()

    def run(self, conn) -> BenchmarkResult:
        series = {QUERY_JOIN: ([], []), QUERY_SUBQUERY: ([], []), QUERY_EXISTS: ([], [])}

        with conn.cursor() as cur:
            for threshold in THRESHOLDS:
                for query, (times, rows_fetched) in series.items():
                    rows, elapsed = measure(cur, query, (threshold,))
                    times.append(elapsed)
                    rows_fetched.append(rows)

        q1, q2, q3 = (
            QueryResult(
                name=name, query=query.strip(),
                times=series[query][0], limits=THRESHOLDS, rows_fetched=series[query][1],
            )
            for name, query in (
                ("JOIN", QUERY_JOIN),
                ("IN (subquery)", QUERY_SUBQUERY),
                ("EXISTS", QUERY_EXISTS),
            )
        )

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2, q3],
            comparison_table=self._build_comparison(q1, q2, q3),
            plot_buffer=self._build_plot(q1, q2, q3),
            explain_plans={
                q.name: run_explain(conn, q.query, (EXPLAIN_THRESHOLD,))
                for q in (q1, q2, q3)
            },
        )

    def teardown(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {ORDERS}")
            conn.commit()

    def _build_comparison(self, q1, q2, q3):
        rows = []
        for i, threshold in enumerate(q1.limits):
            rows.append({
                "amount >": threshold,
                "rows_matched": q1.rows_fetched[i],
                "join": f"{q1.times[i]:.2f} ms",
                "in_subquery": f"{q2.times[i]:.2f} ms",
                "exists": f"{q3.times[i]:.2f} ms",
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2, q3):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        for query, marker in ((q1, "o"), (q2, "s"), (q3, "^")):
            ax.plot(query.limits, query.times, marker=marker, label=query.name)
        ax.set_title(self.title)
        ax.set_xlabel("amount > threshold")
        ax.set_ylabel("Median execution time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
