#!/bin/bash
# E2E Test Runner Script
# This script sets up the environment variables needed for local E2E testing

# Load .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Override CHROMA_HOST for local testing
export CHROMA_HOST=localhost

# Set database credentials if not already set
export DB_HOST=${DB_HOST:-127.0.0.1}
export DB_NAME=${DB_NAME:-papers}
export DB_USER=${DB_USER:-user}
export DB_PASSWORD=${DB_PASSWORD:-password}
export DB_PORT=${DB_PORT:-5432}

# Add /usr/local/bin to PATH for Docker and PostgreSQL tools
export PATH="/usr/local/bin:$PATH"

# Run pytest with the provided arguments
pytest "$@"
