#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set default values if not provided
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-papers}
export DB_USER=${DB_USER:-user}
export DB_PASSWORD=${DB_PASSWORD:-password}

# Set pgroll connection string
export PGROLL_PG_URL="postgres://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=disable"

echo "pgroll Migration Status"
echo "======================="
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Check if pgroll is installed
if ! command -v pgroll &> /dev/null; then
  echo "pgroll is not installed!"
  echo "Install it with: brew install pgroll"
  exit 1
fi

# Get pgroll status
echo "Fetching migration status..."
echo ""

if pgroll status; then
  echo ""
  echo "Database migrations are up to date!"
else
  echo ""
  echo "There may be pending migrations"
  echo "Run: ./scripts/migrate.sh"
fi

echo ""
echo "Migrations in repository:"
ls -1 migrations/*.json 2>/dev/null | sort -V | while read MIGRATION; do
  echo "   * $(basename $MIGRATION)"
done || echo "   No migrations found"
