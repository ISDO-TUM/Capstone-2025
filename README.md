### Prerequisites

* Python 3.13+
* Pip
* An active OpenAI API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ISDO-TUM/Capstone-2025.git
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
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

### Running the Project
```bash
python app.py