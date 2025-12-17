# Use an official Python runtime as a parent image
FROM golang:1.24-bookworm AS pgroll-builder

# Ensure cgo is enabled (needed by pg_query_go)
ENV CGO_ENABLED=1

# Install pgroll (pin a version for reproducibility)
RUN go install github.com/xataio/pgroll@v0.14.3

FROM python:3.11-slim-bookworm AS production
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install PostgreSQL client tools, wget, jq, and pgroll
RUN apt-get update && \
    apt-get install -y postgresql-client wget jq && \
    rm -rf '/var/lib/apt/lists/*'

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code into the container at /app
COPY . .

# Install only production dependencies
RUN uv sync --locked --no-dev

# Copy the
COPY --from=pgroll-builder /go/bin/pgroll /usr/local/bin/pgroll

# Define environment variables for database connection (these will be overridden at runtime)
ENV DB_HOST="your_remote_db_host"
ENV DB_PORT="5432"
ENV DB_NAME="your_db_name"
ENV DB_USER="your_db_user"
ENV DB_PASSWORD="your_db_password"
ENV OPENAI_API_KEY="your_openai_api_key"
ENV CHROMA_HOST="chromadb"

# Run app.py when the container launches
RUN chmod +x /app/scripts/startup.sh
ENTRYPOINT ["/app/scripts/startup.sh"]
