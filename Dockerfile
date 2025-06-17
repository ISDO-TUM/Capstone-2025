# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Install PostgreSQL client tools (psql + pg_isready)
RUN apt-get update && \
    apt-get install -y postgresql-client-common postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# only production dependencies are typically installed.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# app.py runs on port 5000 (Flask default port)
EXPOSE 7500

# Define environment variables for database connection (these will be overridden at runtime)
ENV DB_HOST="your_remote_db_host"
ENV DB_PORT="5432"
ENV DB_NAME="your_db_name"
ENV DB_USER="your_db_user"
ENV DB_PASSWORD="your_db_password"
ENV OPENAI_API_KEY="your_openai_api_key"

# Run app.py when the container launches
CMD ["python", "app.py"]
