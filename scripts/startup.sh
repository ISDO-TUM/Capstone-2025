#!/bin/sh

echo "Starting application initialization..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" > /dev/null 2>&1; do
  echo "Database not ready yet, waiting..."
  sleep 2
done

echo "Database is ready!"

# Run migrations with pgroll (if available)
if command -v pgroll > /dev/null 2>&1; then
  echo "Running database migrations with pgroll..."
  export PGROLL_PG_URL="postgres://${DB_USER:-user}:${DB_PASSWORD:-password}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-papers}?sslmode=disable"
  pgroll init || true
  pgroll migrate migrations/ --complete || true
  echo "Migrations complete!"
else
  echo "pgroll not found, skipping migrations..."
fi

# Start the application
echo "Starting Flask application..."
# Try uv first, fallback to python
if command -v uv > /dev/null 2>&1; then
  exec uv run python app.py
else
  exec python app.py
fi
