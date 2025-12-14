"""
Centralized configuration loader for the Capstone project.

This module must be imported before any other project modules to ensure
environment variables are loaded consistently across the application.

All environment variable loading happens here in one place to ensure:
- Consistent behavior across all modules
- Easy testing with mocked configurations
- Single source of truth for configuration
- Clear documentation of all required environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables once at module import
load_dotenv()

# Test mode configuration
TEST_MODE = os.getenv("TEST_MODE") == "true"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "papers")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Clerk Authentication
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
CLERK_FRONTEND_API_URL = os.getenv("CLERK_FRONTEND_API_URL")
HOSTNAME = os.getenv("HOSTNAME")

# ChromaDB configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")  # default for Docker
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Newsletter update interval (days)
DAYS_FOR_UPDATE = 7


def validate_required_env_vars():
    """
    Validate that all required environment variables are set.

    Raises:
        ValueError: If any required environment variable is missing.
    """
    if TEST_MODE:
        # In test mode, don't validate Clerk vars
        return

    required_vars = {
        "CLERK_SECRET_KEY": CLERK_SECRET_KEY,
        "CLERK_PUBLISHABLE_KEY": CLERK_PUBLISHABLE_KEY,
        "CLERK_FRONTEND_API_URL": CLERK_FRONTEND_API_URL,
        "HOSTNAME": HOSTNAME,
    }

    missing = [name for name, value in required_vars.items() if not value]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
