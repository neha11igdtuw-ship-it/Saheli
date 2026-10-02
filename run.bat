@echo off
echo ========================================
echo Saheli - Women Safety App
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate
echo.

echo Installing/Updating dependencies...
pip install -r requirements.txt
echo.

echo Starting Saheli application...
echo.
echo Access the app at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause

