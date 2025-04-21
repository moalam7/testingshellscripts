#!/bin/bash
# Script to expose the Oracle DB Monitor API with FastAPI to the internet

echo "Exposing Oracle DB Monitor API with FastAPI to the internet..."

# Check if the API is running
if ! pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "API is not running. Starting it now..."
    ./deploy.sh
    
    # Give it a moment to start up
    sleep 3
    
    # Check again
    if ! pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo "Failed to start the API. Please check the logs."
        exit 1
    fi
fi

echo "API is running. You can access it locally at: http://localhost:5000"
echo ""
echo "To expose this API to the internet for Dynatrace to access, you have several options:"
echo ""
echo "1. Use a reverse proxy like Nginx or Apache with proper SSL/TLS"
echo "2. Use a cloud service like AWS, Azure, or GCP"
echo "3. Use a tunneling service like ngrok or Cloudflare Tunnel"
echo ""
echo "For a quick test with ngrok (if installed):"
echo "ngrok http 5000"
echo ""
echo "For production use, we recommend option 1 or 2 with proper security measures."
echo "Remember to configure your firewall to allow incoming connections on the exposed port."
echo ""
echo "FastAPI provides automatic API documentation at:"
echo "http://localhost:5000/docs - Swagger UI"
echo "http://localhost:5000/redoc - ReDoc"
