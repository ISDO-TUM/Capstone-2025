#!/usr/bin/env bash
# Run pytest tests using the uv-managed virtual environment
# Usage: ./run_tests.sh [pytest arguments]

set -e

# Activate the virtual environment and run pytest
source .venv/bin/activate
pytest "$@"
