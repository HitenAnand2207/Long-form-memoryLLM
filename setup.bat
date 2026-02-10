@echo off
REM Setup script for Long-Form Memory System (Windows)

echo ========================================
echo Long-Form Memory System Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from python.org
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip

echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/5] Creating data directories...
if not exist "data" mkdir data
if not exist "data\embeddings" mkdir data\embeddings

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run demo: python src\demo.py
echo   3. Run API server: python src\api_server.py
echo   4. Run evaluation: python src\evaluate.py
echo.
pause