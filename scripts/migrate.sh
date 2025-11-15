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

echo "Running pgroll migrations..."
echo "Database: $DB_HOST:$DB_PORT/$DB_NAME"
echo ""

# Check if pgroll is installed
if ! command -v pgroll &> /dev/null; then
  echo "pgroll is not installed!"
  echo "Install it with: brew install pgroll"
  exit 1
fi

# Initialize pgroll if not already initialized
echo "Initializing pgroll..."
pgroll init 2>&1 | grep -v "already initialized" || true

# Get all migration files sorted
MIGRATIONS=$(ls -1 migrations/*.json 2>/dev/null | sort -V)

if [ -z "$MIGRATIONS" ]; then
  echo " No migrations found in migrations/ directory"
  exit 0
fi

echo "Found migrations:"
for MIGRATION in $MIGRATIONS; do
  echo "   - $(basename $MIGRATION)"
done
echo ""

# Apply all migrations
for migration in $MIGRATIONS; do
  MIGRATION_NAME=$(basename "$migration" .json)
  
  echo "Applying migration: $MIGRATION_NAME"
  
  if pgroll start "$migration" 2>&1 | grep -q "New version"; then
    echo "   Migration started"
    
    # Wait a moment for migration to be ready
    sleep 1
    
    # Complete the migration
    if pgroll complete 2>&1; then
      echo "   Migration completed successfully"
    else
      echo "   Migration may be in progress"
    fi
  else
    echo "   Migration may already be applied"
  fi
  
  echo ""
done

echo "All migrations processed!"
echo ""
echo "Migration status:"
pgroll status 2>/dev/null || echo "Migration tracking active"
