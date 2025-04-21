from flask import Flask, jsonify, render_template_string
import oracledb
import os
import time
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# Database connection parameters
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 1521)),
    'service_name': os.environ.get('DB_SERVICE_NAME', 'ORCLPDB1'),
    'user': os.environ.get('DB_USER', 'system'),
    'password': os.environ.get('DB_PASSWORD', 'oracle'),
}

# HTML template with auto-refresh functionality
HEALTH_PAGE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Oracle Database Health Monitor</title>
    <meta http-equiv="refresh" content="{{ refresh_interval }}">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        .status {
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .up {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .down {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            margin-top: 20px;
            background-color: #e2e3e5;
            padding: 10px;
            border-radius: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .refresh-control {
            margin-top: 20px;
        }
        .refresh-control select {
            padding: 5px;
        }
        .timestamp {
            font-size: 0.8em;
            color: #666;
            margin-top: 15px;
        }
    </style>
    <script>
        // Function to update refresh interval
        function updateRefreshInterval() {
            var interval = document.getElementById('refresh-interval').value;
            window.location.href = '/?refresh=' + interval;
        }
        
        // Function to manually refresh the page
        function refreshNow() {
            window.location.reload();
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Oracle Database Health Monitor</h1>
        
        <div class="status {{ 'up' if status == 'UP' else 'down' }}">
            <h2>Status: {{ status }}</h2>
            <p><strong>Database:</strong> {{ database }}</p>
            <p><strong>Response Time:</strong> {{ response_time_ms }} ms</p>
            {% if error %}
            <p><strong>Error:</strong> {{ error }}</p>
            {% endif %}
        </div>
        
        <div class="refresh-control">
            <p>Auto-refresh interval: 
                <select id="refresh-interval" onchange="updateRefreshInterval()">
                    <option value="60" {{ 'selected' if refresh_interval == 60 }}>1 minute</option>
                    <option value="300" {{ 'selected' if refresh_interval == 300 }}>5 minutes</option>
                    <option value="600" {{ 'selected' if refresh_interval == 600 }}>10 minutes</option>
                    <option value="1800" {{ 'selected' if refresh_interval == 1800 }}>30 minutes</option>
                    <option value="3600" {{ 'selected' if refresh_interval == 3600 }}>1 hour</option>
                    <option value="0" {{ 'selected' if refresh_interval == 0 }}>Disabled</option>
                </select>
                <button onclick="refreshNow()">Refresh Now</button>
            </p>
        </div>
        
        <div class="info">
            <p>This page automatically checks the health of your Oracle database at the specified interval.</p>
            <p>Each check establishes a new connection to the database and closes it immediately after the check.</p>
            <p>No persistent connections are maintained between checks.</p>
        </div>
        
        <p class="timestamp">Last checked: {{ timestamp }}</p>
    </div>
</body>
</html>
'''

def get_connection():
    """Create and return a database connection with timeout"""
    dsn = oracledb.makedsn(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        service_name=DB_CONFIG['service_name']
    )
    
    # Set timeout to 5 seconds for connection attempt
    connection = oracledb.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        dsn=dsn,
        timeout=5  # 5 second timeout for connection attempt
    )
    return connection

@app.route('/', methods=['GET'])
def index():
    """Redirect to health page"""
    refresh_interval = request.args.get('refresh', default=300, type=int)
    return redirect(url_for('health_check', refresh=refresh_interval))

@app.route('/health', methods=['GET'])
def health_check():
    """Check if Oracle database is up and return status for Dynatrace to monitor"""
    from flask import request
    
    # Get refresh interval from query parameter, default to 5 minutes (300 seconds)
    refresh_interval = request.args.get('refresh', default=300, type=int)
    
    start_time = time.time()
    status = "DOWN"
    error_message = None
    database_info = f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}"
    
    try:
        # Create a new connection for each health check
        connection = get_connection()
        
        with connection:
            # Execute a simple query to verify the connection is working
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
        
        # If we get here, the database is up
        status = "UP"
        
    except Exception as e:
        # If any error occurs, the database is considered down
        error_message = str(e)
    
    finally:
        # Calculate response time
        response_time = round((time.time() - start_time) * 1000)
        current_time = datetime.datetime.now().isoformat()
        
        # Check if the request wants JSON or HTML
        if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
            # Return JSON response for API clients (like Dynatrace)
            response_data = {
                "status": status,
                "database": database_info,
                "response_time_ms": response_time,
                "timestamp": current_time
            }
            
            if error_message:
                response_data["error"] = error_message
                
            return jsonify(response_data), 200 if status == "UP" else 503
        else:
            # Return HTML page with auto-refresh for human viewers
            return render_template_string(
                HEALTH_PAGE_TEMPLATE,
                status=status,
                database=database_info,
                response_time_ms=response_time,
                error=error_message,
                timestamp=current_time,
                refresh_interval=refresh_interval if refresh_interval > 0 else ""
            )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
