#!/bin/bash
# Script to install dependencies and run the Oracle DB Monitor API with FastAPI

echo "Setting up Oracle DB Monitor with FastAPI..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if .env file exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your Oracle database connection details."
    echo "Then run this script again."
    exit 0
fi

# Run the test connection script
echo "Testing database connection..."
python3 test_connection.py

# Check if the test was successful
if [ $? -ne 0 ]; then
    echo "Database connection test failed. Please check your connection details in the .env file."
    exit 1
fi

# Run the API
echo "Starting the FastAPI server..."
python3 -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
