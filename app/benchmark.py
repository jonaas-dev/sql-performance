import time
import io
import base64
import matplotlib.pyplot as plt
import pandas as pd

from app.config import START, STEP, QUERY_1_NAME, QUERY_2_NAME, TMP_DIR, QUERIES_DIR


def measure_query_time(query, limit, cursor):
    try:
        start_time = time.perf_counter()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000
        return rows, execution_time
    except Exception as e:
        return None, str(e)


def get_query_from_file(filename):
    with open(filename, 'r') as file:
        return file.read()


def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return df


def generate_comparison_table(query_1_results, query_2_results):
    comparison_data = []
    for q1, q2 in zip(query_1_results, query_2_results):
        q1_time = q1['time']
        q2_time = q2['time']
        diff = q1_time - q2_time
        comparison_data.append({
            'limit': q1['limit'],
            'query_1_time': f'{q1_time:.2f} ms',
            'query_2_time': f'{q2_time:.2f} ms',
            'time_difference': f'{diff:.2f} ms'
        })
    return pd.DataFrame(comparison_data)


def generate_plot_from_csv(file_1, file_2):
    df1 = pd.read_csv(file_1)
    df2 = pd.read_csv(file_2)

    plt.figure(figsize=(10, 6))
    plt.plot(df1['limit'], df1['time'], marker='o', label=QUERY_1_NAME)
    plt.plot(df2['limit'], df2['time'], marker='s', label=QUERY_2_NAME)
    plt.title('SQL Query Execution Time Comparison')
    plt.xlabel('LIMIT')
    plt.ylabel('Execution Time (milliseconds)')
    plt.xticks(df1['limit'])
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


def run_benchmark(conn):
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    limits = list(range(START, 0, -STEP))
    query_1 = get_query_from_file(str(QUERIES_DIR / 'query_1.sql'))
    query_2 = get_query_from_file(str(QUERIES_DIR / 'query_2.sql'))

    query_1_results = []
    query_2_results = []

    with conn.cursor() as cursor:
        for limit in limits:
            rows_1, time_1 = measure_query_time(query_1, limit, cursor)
            rows_2, time_2 = measure_query_time(query_2, limit, cursor)
            query_1_results.append({'limit': limit, 'time': time_1, 'rows': rows_1})
            query_2_results.append({'limit': limit, 'time': time_2, 'rows': rows_2})

    save_to_csv(
        [{'limit': r['limit'], 'time': r['time']} for r in query_1_results],
        str(TMP_DIR / 'query_1_results.csv')
    )
    save_to_csv(
        [{'limit': r['limit'], 'time': r['time']} for r in query_2_results],
        str(TMP_DIR / 'query_2_results.csv')
    )

    plot_buffer = generate_plot_from_csv(
        str(TMP_DIR / 'query_1_results.csv'),
        str(TMP_DIR / 'query_2_results.csv')
    )
    plot_data = base64.b64encode(plot_buffer.getvalue()).decode('utf-8')

    comparison_table = generate_comparison_table(query_1_results, query_2_results)
    save_to_csv(comparison_table, str(TMP_DIR / 'comparison_table.csv'))

    return plot_data, comparison_table
