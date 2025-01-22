from flask import Flask, jsonify, Response
import psycopg2
import os
import time
import matplotlib.pyplot as plt
import io

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

def measure_query_time(query, limit):
    """Function to execute a query with a limit and measure its execution time."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Start timing
        start_time = time.perf_counter()
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        # End timing
        end_time = time.perf_counter()

        cursor.close()
        conn.close()
        
        execution_time = end_time - start_time
        return rows, execution_time
    except Exception as e:
        return None, str(e)

def generate_plot(results):
    """Generate a plot comparing execution times."""
    # Extract limits and times
    limits = [result['limit'] for result in results]
    select_all_times = [result['select_all_time'] for result in results]
    select_id_times = [result['select_id_time'] for result in results]

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(limits, select_all_times, marker='o', label='SELECT *')
    plt.plot(limits, select_id_times, marker='s', label='SELECT id')
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
