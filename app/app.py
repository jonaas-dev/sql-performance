from app.utils import generate_plot, measure_query_time
from flask import Flask, jsonify, Response

# Initialize the Flask app
app = Flask(__name__)


@app.route('/')
def index():
    """Route to test and return query execution times."""
    results = []
    limits = [1, 2, 3, 5, 10, 20]
    
    for limit in limits:
        # Test 'SELECT *'
        query_all = "SELECT * FROM users LIMIT %s"
        _, time_all = measure_query_time(query_all, limit)
        
        # Test 'SELECT id'
        query_id = "SELECT id FROM users LIMIT %s"
        _, time_id = measure_query_time(query_id, limit)
        
        if isinstance(time_all, float) and isinstance(time_id, float):
            results.append({
                'limit': limit,
                'select_all_time': time_all,
                'select_id_time': time_id,
            })
        else:
            results.append({
                'limit': limit,
                'error': {'select_all': time_all, 'select_id': time_id}
            })

    # Generate and return the plot as an image
    plot_buffer = generate_plot(results)
    return Response(plot_buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
