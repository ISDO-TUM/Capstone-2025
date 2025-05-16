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
    pip install -r requirements.txt -r requirements-dev.txt
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
### Local Development
* Before creating a PR, make sure that your local commits go through pre-commit hooks, which check
for formatting, linting and security issues. They also update the needed modules in
**requirements.txt**. First you have to set this up:
1. Make sure you install `pre-commit` and `pigar` modules with:
```
pip install -r requirements-dev.txt
```

2. Issue the following command in your virtual environment:
```
pre-commit install
```

3. Pre-commit hooks are triggered on commits and they can also make changes to the files
   (formatting and updating **requirements.txt**). In this case, if the pre-commit hook has run and
made changes to your files, you have to stage your changes again and commit them again:
```
git add .
git commit -m "Your commit message"
```
### Running the Project
```bash
python app.py
