@echo off
setlocal
echo.
echo ====== Setup dependencies for rq2_project ======
echo This will create a virtual environment in .venv and install Python packages.
echo.

REM Create virtual environment
python -m venv .venv
if %errorlevel% neq 0 (
  echo Failed to create virtual environment. Ensure Python 3.10+ is installed and in PATH.
  pause
  exit /b 1
)

echo Upgrading pip in virtual environment...
.venv\Scripts\python -m pip install --upgrade pip

echo Installing required packages from rq2_project\requirements.txt ...
.venv\Scripts\python -m pip install -r rq2_project\requirements.txt
if %errorlevel% neq 0 (
  echo pip install failed. Try opening PowerShell as Administrator and re-run this script.
  pause
  exit /b 1
)

echo.
echo Dependencies installed successfully.
echo To run the app, use:
echo    .venv\Scripts\python -m streamlit run rq2_project\app.py
echo.
pause
