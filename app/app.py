from flask import Flask, jsonify, Response, render_template, request
import psycopg2
import os
import time
import matplotlib.pyplot as plt
import io

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
        # Start timing
        start_time = time.perf_counter()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        # End timing
        end_time = time.perf_counter()

        execution_time = end_time - start_time
        return rows, execution_time
    except Exception as e:
        return None, str(e)

def measure_average_time(query, limit, cursor, repetitions=50):
    """Measure average time for a query executed multiple times."""
    times = []
    for _ in range(repetitions):
        _, execution_time = measure_query_time(query, limit, cursor)
        if isinstance(execution_time, float):
            times.append(execution_time)
    return sum(times) / len(times) if times else None

def get_query_from_file(filename):
    """Function to read and return a SQL query from a file."""
    with open(filename, 'r') as file:
        query = file.read()
    return query

def generate_plot(results):
    """Generate a plot comparing execution times."""
    # Extract limits and times
    limits = [result['limit'] for result in results]
    select_all_times = [result['query_1_time'] for result in results]
    select_id_times = [result['query_2_time'] for result in results]

    # Create the plot
    plt.figure(figsize=(12, 8))
    plt.plot(limits, select_all_times, marker='o', label='Query 1')
    plt.plot(limits, select_id_times, marker='s', label='Query 2')
    plt.title('SQL Query Execution Time Comparison')
    plt.xlabel('LIMIT')
    plt.ylabel('Execution Time (seconds)')
    plt.xticks(limits)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    # Save plot to a BytesIO buffer
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
    return render_template('loading.html')

@app.route('/generate')
def index():
    """Route to test and return query execution times."""
    results = []
    limits = list(range(10000000, -1, -1000000))

    # Load queries once to avoid redundant file reads
    query_1 = get_query_from_file('./queries/query_1.sql')
    query_2 = get_query_from_file('./queries/query_2.sql')

    # Establish a single database connection for all queries
    conn = get_db_connection()
    cursor = conn.cursor()

    # Warmup queries separately
    measure_query_time(query_1, 100000, cursor)
    measure_query_time(query_2, 100000, cursor)

    for limit in limits:
        # Measure time for query_1
        time_1 = measure_average_time(query_1, limit, cursor)
        
        # Measure time for query_2
        time_2 = measure_average_time(query_2, limit, cursor)

        # Store the results
        if time_1 is not None and time_2 is not None:
            results.append({
                'limit': limit,
                'query_1_time': time_1,
                'query_2_time': time_2,
            })
        else:
            results.append({
                'limit': limit,
                'error': {'query_1': time_1, 'query_2': time_2}
            })

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Generate and return the plot as an image
    plot_buffer = generate_plot(results)
    return Response(plot_buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
