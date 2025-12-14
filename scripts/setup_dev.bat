@echo off
echo Setting up development environment...

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.11+.
    exit /b 1
)

REM Create venv if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env if not exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Setup complete! To activate: call venv\Scripts\activate
pause
