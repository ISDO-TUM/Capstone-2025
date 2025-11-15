# Use an official Python runtime as a parent image
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install PostgreSQL client tools, wget, jq, and pgroll
RUN apt-get update && \
    apt-get install -y postgresql-client wget jq && \
    wget -O /usr/local/bin/pgroll https://github.com/xataio/pgroll/releases/download/v0.14.3/pgroll.linux.amd64 && \
    chmod +x /usr/local/bin/pgroll && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code into the container at /app
COPY . .

# Install only production dependencies
RUN uv sync --locked --no-dev

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
CMD ["uv", "run", "app.py", "--no-dev"]
