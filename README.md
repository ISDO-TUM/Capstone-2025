# Capstone-2025: Agentic Paper Recommendation System

A modular, extensible agentic academic paper recommendation system leveraging LLMs, vector search, and modern backend best practices. Designed for multi-step reasoning, project-specific recommendations, and robust filtering, with a focus on maintainability and extensibility.

## Folder Structure

```
Capstone-2025/
├── app.py
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml
├── Dockerfile
├── llm/
│   ├── StategraphAgent.py
│   ├── Agent.py
│   ├── tools/
│   ├── util/
│   ├── Embeddings.py
│   ├── LLMDefinition.py
│   ├── Prompts.py
│   └── ...
├── database/
│   ├── papers_database_handler.py
│   ├── projects_database_handler.py
│   ├── projectpaper_database_handler.py
│   └── ...
├── chroma_db/
│   ├── chroma_vector_db.py
│   ├── Tests/
│   └── ...
├── paper_handling/
│   ├── paper_handler.py
│   └── ...
├── pubsub/
│   └── ...
├── evaluations/
│   └── ...
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── dashboard.html
│   ├── create_project.html
│   ├── project_overview.html
│   └── pubsub_home.html
├── utils/
│   └── status.py
├── Notification/
│   └── SendMail.py
├── paper_ranking/
└── ...
```

---

## Technical Architecture & Project Overview

### System Architecture

The Capstone-2025 project is a modular, extensible academic paper recommendation system that leverages LLMs, vector search, and modern backend best practices. The system is designed for multi-step reasoning, project-specific recommendations, and robust filtering, with a focus on maintainability and extensibility.

#### **Key Components**
- **Flask API (`app.py`)**: Exposes REST endpoints for project management, recommendations, ratings, newsletter, and PDF extraction. Orchestrates the agent and handles all frontend/backend communication.
- **Stategraph Agent (`llm/StategraphAgent.py`)**: The main orchestrator for multi-step academic search and filtering. Implements a state machine with nodes for input handling, out-of-scope detection, quality control, paper ingestion, vector search, filtering, and result storage.
- **Tools Layer (`llm/tools/`)**: Implements modular tools for paper ingestion, filtering, ranking, and project management. Tools are registered and aggregated for agent use.
- **Database Handlers (`database/`)**: Encapsulate all database operations for papers, projects, and project-paper links. Ensure robust, transactional access to PostgreSQL.
- **ChromaDB Vector Search (`chroma_db/chroma_vector_db.py`)**: Handles storage and retrieval of paper embeddings, and performs similarity search for recommendations.
- **Paper Handling (`paper_handling/`)**: Utilities for fetching, cleaning, and summarizing papers from OpenAlex, and for processing recommendations.
- **LLM Integration (`llm/LLMDefinition.py`, `llm/Embeddings.py`)**: Handles LLM instantiation, prompt management, and embedding generation.
- **Utility Modules (`llm/util/`, `utils/`)**: Provide custom filtering, log formatting, and status code management.

### Main Flows

#### **1. Project Creation & Paper Ingestion**
- User creates a project via the API.
- The agent (via `update_papers_for_project`) fetches relevant papers from OpenAlex, stores them in the database, and generates embeddings for ChromaDB.

#### **2. Recommendation Flow**
- User requests recommendations for a project.
- The agent runs a multi-step workflow:
  1. **Input Handling**: Extracts query and project ID.
  1. **Out-of-Scope Detection**: Filters out non-research queries.
  1. **Quality Control**: Reformulates, broadens, narrows, or splits queries as needed.
  1. **Paper Ingestion**: Ensures the latest papers are available for the project.
  1. **Vector Search**: Retrieves the most relevant papers using ChromaDB similarity search.
  1. **Filtering**: Applies natural language or user-defined filters, always preserving vector search order and limiting to top 10 results.
  1. **Result Storage**: Stores recommendations and relevance summaries for the project.

#### **3. Paper Rating & Replacement**
- User rates a paper; if the rating is low, the system automatically finds and recommends a replacement using vector search and project-specific filtering.

#### **4. Newsletter & PubSub**
- The system can mark papers for newsletter delivery and manage seen/unseen status for pubsub flows.

### Backend Structure

- **Modular Tools**: All major actions (ingestion, filtering, ranking, etc.) are implemented as tools, making it easy to add, remove, or update functionality.
- **Stategraph Orchestration**: The agent is built as a state machine, with each node responsible for a single step and robust error handling/logging.
- **Database Isolation**: Projects, papers, and embeddings are always isolated by project ID, ensuring no cross-project leakage.
- **Order Preservation**: The order of papers from vector search is preserved throughout the pipeline, ensuring the most relevant results are always prioritized.
- **Local Testing Policy**: All files with local main methods for testing have these blocks commented out and clearly marked for local use only.

---

### Prerequisites

* [uv](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1)
* Python 3.11 (managed by uv)
* An active OpenAI API Key
* Docker Desktop (or docker + docker-compose)

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ISDO-TUM/Capstone-2025.git
    ```

1.  **Replicate the virtual environment with all dependencies:**
    ```bash
    uv sync
    ```

1.  **Set up Environment Variables:**
    This project requires an OpenAI API key to function. You need to set the `OPENAI_API_KEY` environment variable.

    **Option 1: Using a `.env` file (Recommended for local development)**
    * Create a file named `.env` in the root project directory.
    * Add your OpenAI API key to this file:
        ```env
        OPENAI_API_KEY="your_actual_openai_api_key_here"
        ```
    * The `.env` file is included in `.gitignore` and should **not** be committed to version control. An example can be seen in `.env.example`. It shows what variables are needed:
        ```env
        # .env.example
        OPENAI_API_KEY="YOUR_OPENAI_API_KEY_GOES_HERE"
        ```

    **Option 2: Setting system environment variables**
    * **Linux/macOS:**
        ```bash
        export OPENAI_API_KEY="your_actual_openai_api_key_here"
        ```
        (Add this to your `~/.bashrc` or `~/.zshrc` for persistence across sessions).
    * **Windows (Command Prompt):**
        ```cmd
        set OPENAI_API_KEY="your_actual_openai_api_key_here"
        ```
    * **Windows (PowerShell):**
        ```powershell
        $Env:OPENAI_API_KEY="your_actual_openai_api_key_here"
        ```
        (For permanent storage on Windows, search for "environment variables" in the Start Menu).

1. **Set up Database Environment Variables:**
    This project uses also a **PostgreSQL** database, and you must connect to a local copy of it.
    You need to set also the environment variables for the connection to it (used for **Docker**):
    ```
   DB_HOST="your_remote_postgresql_server_ip_or_hostname" Used only when connecting to the remote
    DB_PORT="5432"
    DB_NAME="papers"
    DB_USER="your_username_for_postgresql"
    DB_PASSWORD="your_password_for_postgresql"
   ```

1.  **Running individual files in the project:**
    ```bash
    uv run path/to/file
    ```
    This command also updates dependencies according to uv.lock/pyproject.toml if changes have been made, e.g. after you pull some new changes.

1. (For completeness) If you want to add a new dependency it can be done using:
    ```bash
    uv add dependency-name
    ```


### Running the Project
```bash
docker compose up -d
```

---

## Database Migrations

This project uses [pgroll](https://github.com/xataio/pgroll) for zero-downtime PostgreSQL schema migrations.

Migrations run automatically when you start the container:
```bash
docker compose up -d
```

For detailed information about creating, running, and troubleshooting migrations, see the [Migrations Guide](migrations/README.md).

### Quick Reference

**Run migrations manually:**
```bash
docker compose exec web pgroll migrate
```

**Create a new migration:**
```bash
./scripts/new_migration.sh migration_name
```

**Check migration status:**
```bash
docker compose exec web pgroll status
```

**Helper scripts:**
- `scripts/migrate.sh` - Run all pending migrations
- `scripts/new_migration.sh` - Generate new migration file
- `scripts/migration_status.sh` - Check migration status

For more details, examples, and troubleshooting, see [migrations/README.md](migrations/README.md).

---

### Testing

The project includes comprehensive end-to-end (E2E) tests using Playwright and Pytest. Tests run automatically in CI/CD on pull requests and pushes to main.

For local testing and debugging, see the complete testing guide:
- **[E2E Testing Documentation](tests/e2e/README.md)**

## Testing

The project includes comprehensive end-to-end (E2E) tests using Playwright. For detailed testing documentation, see [tests/e2e/README.md](tests/e2e/README.md).

### Quick Test Commands
```bash
# Run all E2E tests
cd tests/e2e/
./run_e2e_tests.sh .
```
---

### Contribution workflow
* Before creating a PR, make sure that your local commits go through pre-commit hooks, which check
for formatting, linting and security issues. They also update the needed modules in
**requirements.txt**. First you have to set this up:
1.  Make sure you install `pre-commit` and `pigar` modules with:
    ```
    pip install -r requirements-dev.txt
    ```

1.  Issue the following command in your virtual environment (needed only after initial setup):
    ```
    pre-commit install
    ```

1.  Pre-commit hooks are triggered on commits and they can also make changes to the files
    (formatting and updating **requirements.txt**). In this case, if the pre-commit hook has run and
    made changes to your files, you have to stage your changes again and commit them again:
    ```
    git add .
    git commit -m "Your commit message"
    ```

1.  If **pigar** has made undesirable changes to the **requirements.txt** file, you can commit with:

    ```
    git commit -m "Your commit message" --no-verify
    ```

---

### Extension Points

- **Adding New Tools**: Implement a new function in `llm/tools/`, register it in `Tools_aggregator.py`, and then create a new node in `llm/StategraphAgent.py` and add the node to the existing graph.
- **Custom Filters**: Extend `llm/util/agent_custom_filter.py` to add new operators or filtering logic.
- **LLM/Embedding Models**: Update `llm/LLMDefinition.py` and `llm/Embeddings.py` to use new models or providers.
- **Frontend Integration**: The API is designed to be frontend-agnostic and can be integrated with any modern web UI.

### Best Practices for Contributors

- **Follow the modular tool pattern** for new features.
- **Write clear docstrings** for all new functions, classes, and files.
- **Comment out local test entrypoints** and mark them for local use only.
- **Use pre-commit hooks** for formatting, linting, and security checks.
- **Write tests for new features** and use the provided test scripts as templates.
- **Document all new environment variables** and configuration options in the README.

### Environment & Deployment Notes

- **Docker Compose** is used for local development and deployment, with services for the web app, PostgreSQL, and ChromaDB.
- **Environment variables** are used for all secrets and configuration; see `.env.example` for required variables.
- **ChromaDB** can be run locally or in Docker; the system will auto-detect the host based on environment.
- **All local test entrypoints are commented out** and should only be used for development/debugging.

---

For further details, see the docstrings in each module and the comments in the codebase. For questions or contributions, please open an issue or pull request on GitHub.
