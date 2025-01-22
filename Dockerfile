# Use a Python base image (replace version if necessary)
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install dependencies (including Gunicorn)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code to the container
COPY . /app/

# Expose the port your app will run on (8000 by default for Gunicorn)
EXPOSE 8000

# Run the Flask app with Gunicorn
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "app.app:app", "--reload"]
