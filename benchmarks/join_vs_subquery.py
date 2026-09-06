import time
import io
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pandas as pd

from benchmarks.base import BenchmarkBase, BenchmarkResult, QueryResult
from benchmarks.registry import register
from app.config import TMP_DIR
from app.benchmark import run_explain


@register
class JoinVsSubqueryBenchmark(BenchmarkBase):
    name = "join_vs_subquery"
    title = "JOIN vs subquery for filtering"
    description = "Compares JOIN and IN (subquery) for relational filtering"
    required_tables = ["users"]

    def setup(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS orders")
            cur.execute("""
                CREATE TABLE orders (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    amount DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                INSERT INTO orders (user_id, amount)
                SELECT id, (random() * 500)::DECIMAL(10,2)
                FROM users
                WHERE random() < 0.3
            """)
            conn.commit()

    def run(self, conn) -> BenchmarkResult:
        query_join = """
            SELECT u.id, u.name, u.email, o.amount
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE o.amount > %s
        """
        query_subquery = """
            SELECT id, name, email
            FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE amount > %s)
        """
        query_exists = """
            SELECT id, name, email
            FROM users u
            WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > %s)
        """

        thresholds = [50, 100, 200, 300, 400]
        q1_times, q2_times, q3_times = [], [], []
        q1_rows, q2_rows, q3_rows = [], [], []

        with conn.cursor() as cur:
            for t in thresholds:
                r1, t1 = self._measure(query_join, (t,), cur)
                r2, t2 = self._measure(query_subquery, (t,), cur)
                r3, t3 = self._measure(query_exists, (t,), cur)
                q1_times.append(t1)
                q2_times.append(t2)
                q3_times.append(t3)
                q1_rows.append(r1)
                q2_rows.append(r2)
                q3_rows.append(r3)

        q1 = QueryResult(
            name="JOIN", query=query_join.strip(),
            times=q1_times, limits=thresholds, rows_fetched=q1_rows,
        )
        q2 = QueryResult(
            name="IN (subquery)", query=query_subquery.strip(),
            times=q2_times, limits=thresholds, rows_fetched=q2_rows,
        )
        q3 = QueryResult(
            name="EXISTS", query=query_exists.strip(),
            times=q3_times, limits=thresholds, rows_fetched=q3_rows,
        )

        comparison = self._build_comparison(q1, q2, q3)
        plot = self._build_plot(q1, q2, q3)

        explain_plans = {
            q1.name: run_explain(conn, q1.query, (100,)),
            q2.name: run_explain(conn, q2.query, (100,)),
            q3.name: run_explain(conn, q3.query, (100,)),
        }

        return BenchmarkResult(
            name=self.name, title=self.title, description=self.description,
            queries=[q1, q2, q3], comparison_table=comparison, plot_buffer=plot,
            explain_plans=explain_plans,
        )

    def teardown(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS orders")
            conn.commit()

    def _measure(self, query, params, cursor):
        start = time.perf_counter()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000
        return len(rows), elapsed

    def _build_comparison(self, q1, q2, q3):
        rows = []
        for i, t in enumerate(q1.limits):
            rows.append({
                "amount >": t,
                "join": f"{q1.times[i]:.2f} ms",
                "in_subquery": f"{q2.times[i]:.2f} ms",
                "exists": f"{q3.times[i]:.2f} ms",
            })
        return pd.DataFrame(rows)

    def _build_plot(self, q1, q2, q3):
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(q1.limits, q1.times, marker="o", label=q1.name)
        ax.plot(q2.limits, q2.times, marker="s", label=q2.name)
        ax.plot(q3.limits, q3.times, marker="^", label=q3.name)
        ax.set_title(self.title)
        ax.set_xlabel("amount threshold")
        ax.set_ylabel("Execution Time (ms)")
        ax.set_xticks(q1.limits)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        fig.tight_layout()

        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)
        return buf
