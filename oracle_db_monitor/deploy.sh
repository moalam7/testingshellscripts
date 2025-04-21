#!/bin/bash
# Script to deploy the Oracle DB Monitor API

echo "Deploying Oracle DB Monitor API..."

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

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip3 install gunicorn
fi

# Install dependencies if not already installed
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create a .env file with your database connection details."
    echo "You can use the .env.example file as a template."
    exit 1
fi

# Run the test connection script
echo "Testing database connection..."
python3 test_connection.py

# Check if the test was successful
if [ $? -ne 0 ]; then
    echo "Database connection test failed. Please check your connection details in the .env file."
    exit 1
fi

# Start the API server with gunicorn
echo "Starting the API server with gunicorn..."
gunicorn -w 4 -b 0.0.0.0:5000 app:app --daemon

echo "API server started on port 5000"
echo "To check if the server is running: ps aux | grep gunicorn"
echo "To stop the server: pkill gunicorn"
