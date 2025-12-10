@echo off
REM Windows batch script to run pytest tests
REM Usage: run_tests.bat [pytest arguments]
REM Example: run_tests.bat tests/e2e/ -v

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Run pytest with all passed arguments
pytest %*
