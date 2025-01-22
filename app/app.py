from app.utils import generate_plot, measure_query_time
from flask import Flask, jsonify, Response

# Initialize the Flask app
app = Flask(__name__)

def get_query_from_file(filename):
    """Function to read and return a SQL query from a file."""
    with open(filename, 'r') as file:
        query = file.read()
    return query

def measure_average_time(query, limit, repetitions=50):
    times = []
    for _ in range(repetitions):
        _, time = measure_query_time(query, limit)
        if isinstance(time, float):
            times.append(time)
    return sum(times) / len(times) if times else None



@app.route('/')
def index():
    """Route to test and return query execution times."""
    results = []
    limits = list(range(0, 10000001, 1000000))  # Generate limits from 0 to 10,000,000 in steps of 1,000,000

    # Load queries once to avoid redundant file reads
    query_1 = get_query_from_file('./queries/query_1.sql')
    query_2 = get_query_from_file('./queries/query_2.sql')

    # Warmup queries separately
    measure_query_time(query_1, 100000)
    measure_query_time(query_2, 100000)

    for limit in limits:
        # Measure time for query_1
        time_1 = measure_average_time(query_1, limit)
        
        # Measure time for query_2
        time_2 = measure_average_time(query_2, limit)

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

    # Generate and return the plot as an image
    plot_buffer = generate_plot(results)
    return Response(plot_buffer, mimetype='image/png')




if __name__ == '__main__':
    app.run(debug=True)
