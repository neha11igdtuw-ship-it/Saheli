#!/bin/bash

echo "========================================"
echo "Saheli - Women Safety App"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

echo "Activating virtual environment..."
source venv/bin/activate
echo ""

echo "Installing/Updating dependencies..."
pip install -r requirements.txt
echo ""

echo "Starting Saheli application..."
echo ""
echo "Access the app at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""
python app.py

