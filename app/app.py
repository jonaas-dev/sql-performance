from flask import Flask, jsonify, Response, render_template, request
import psycopg2
import os
import time
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

"""
Constants for the query execution time comparison.

START: The starting value for the LIMIT parameter in the queries.
STEP: The step value to decrease the LIMIT parameter in the queries.

The queries will be executed with LIMIT values from START to 0 in steps of STEP.
"""
START = 1000000
STEP = 100000
QUERY_1_NAME = 'Query 1'
QUERY_2_NAME = 'Query 2'



# Initialize the Flask app
app = Flask(__name__)

# Database connection parameters from environment variables
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', 5432)
db_user = os.getenv('DB_USER', 'user')
db_password = os.getenv('DB_PASSWORD', 'password')
db_name = os.getenv('DB_NAME', 'test_db')

def get_db_connection():
    """Function to create and return a connection to the database."""
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    return conn

def measure_query_time(query, limit, cursor):
    """Function to execute a query with a limit and measure its execution time."""
    try:
        start_time = time.perf_counter()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return rows, execution_time
    except Exception as e:
        return None, str(e)

def get_query_from_file(filename):
    """Function to read and return a SQL query from a file."""
    with open(filename, 'r') as file:
        query = file.read()
    return query

def save_to_csv(data, filename):
    """Save query results to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return df

def generate_comparison_table(query_1_results, query_2_results):
    """Generate a table comparing query results with an extra column for time difference."""
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
    """Generate a plot comparing execution times from CSV files."""
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

@app.route('/')
def loading_message():
    """Route to display a loading message or generate the plot immediately."""
    if request.args.get('generate') == 'true':
        return index()  # Directly generate the plot
    return render_template('results.html')



@app.route('/generate')
def index():
    """Route to test and return query execution times."""
    limits = [limit for limit in range(START, 0, -STEP)]
    query_1 = get_query_from_file('./queries/query_1.sql')
    query_2 = get_query_from_file('./queries/query_2.sql')

    query_1_results = []
    query_2_results = []

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            for limit in limits:
                rows_1, time_1 = measure_query_time(query_1, limit, cursor)
                rows_2, time_2 = measure_query_time(query_2, limit, cursor)

                query_1_results.append({'limit': limit, 'time': time_1, 'rows': rows_1})
                query_2_results.append({'limit': limit, 'time': time_2, 'rows': rows_2})

    # Save and process results
    df1 = save_to_csv([{'limit': r['limit'], 'time': r['time']} for r in query_1_results], 'executions_tmp/query_1_results.csv')
    df2 = save_to_csv([{'limit': r['limit'], 'time': r['time']} for r in query_2_results], 'executions_tmp/query_2_results.csv')

    plot_buffer = generate_plot_from_csv('executions_tmp/query_1_results.csv', 'executions_tmp/query_2_results.csv')
    plot_data = base64.b64encode(plot_buffer.getvalue()).decode('utf-8')

    comparison_table = generate_comparison_table(query_1_results, query_2_results)
    
    # Save the comparison table to a CSV file
    comparison_table_filename = 'executions_tmp/comparison_table.csv'
    save_to_csv(comparison_table, comparison_table_filename)
    
    comparison_table_html = comparison_table.to_html(
        index=False,
        classes='table table-striped',
        border=0
    )
    return render_template('results.html', plot_data=plot_data, comparison_table=comparison_table_html)


if __name__ == '__main__':
    app.run(debug=True)
