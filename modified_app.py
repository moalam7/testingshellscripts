from flask import Flask, jsonify, request
import oracledb
import os
import time
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__)

# Multiple database configurations
DB_CONFIGS = {
    'primary': {
        'host': os.environ.get('PRIMARY_DB_HOST', 'localhost'),
        'port': int(os.environ.get('PRIMARY_DB_PORT', 1521)),
        'service_name': os.environ.get('PRIMARY_DB_SERVICE_NAME', 'ORCLPDB1'),
        'user': os.environ.get('PRIMARY_DB_USER', 'system'),
        'password': os.environ.get('PRIMARY_DB_PASSWORD', 'oracle'),
    },
    'secondary': {
        'host': os.environ.get('SECONDARY_DB_HOST', 'localhost'),
        'port': int(os.environ.get('SECONDARY_DB_PORT', 1521)),
        'service_name': os.environ.get('SECONDARY_DB_SERVICE_NAME', 'ORCLPDB2'),
        'user': os.environ.get('SECONDARY_DB_USER', 'system'),
        'password': os.environ.get('SECONDARY_DB_PASSWORD', 'oracle'),
    },
    'reporting': {
        'host': os.environ.get('REPORTING_DB_HOST', 'localhost'),
        'port': int(os.environ.get('REPORTING_DB_PORT', 1521)),
        'service_name': os.environ.get('REPORTING_DB_SERVICE_NAME', 'ORCLPDB3'),
        'user': os.environ.get('REPORTING_DB_USER', 'system'),
        'password': os.environ.get('REPORTING_DB_PASSWORD', 'oracle'),
    },
    'archive': {
        'host': os.environ.get('ARCHIVE_DB_HOST', 'localhost'),
        'port': int(os.environ.get('ARCHIVE_DB_PORT', 1521)),
        'service_name': os.environ.get('ARCHIVE_DB_SERVICE_NAME', 'ORCLPDB4'),
        'user': os.environ.get('ARCHIVE_DB_USER', 'system'),
        'password': os.environ.get('ARCHIVE_DB_PASSWORD', 'oracle'),
    },
    'development': {
        'host': os.environ.get('DEV_DB_HOST', 'localhost'),
        'port': int(os.environ.get('DEV_DB_PORT', 1521)),
        'service_name': os.environ.get('DEV_DB_SERVICE_NAME', 'ORCLPDB5'),
        'user': os.environ.get('DEV_DB_USER', 'system'),
        'password': os.environ.get('DEV_DB_PASSWORD', 'oracle'),
    }
}

def get_connection(db_name):
    """Create and return a database connection for the specified database"""
    if db_name not in DB_CONFIGS:
        raise ValueError(f"Unknown database: {db_name}")
    
    config = DB_CONFIGS[db_name]
    dsn = oracledb.makedsn(
        host=config['host'],
        port=config['port'],
        service_name=config['service_name']
    )
    
    connection = oracledb.connect(
        user=config['user'],
        password=config['password'],
        dsn=dsn
    )
    return connection

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with basic information"""
    endpoints = {
        "/health": "Legacy endpoint - Basic database connectivity check for primary database",
    }
    
    # Add all database-specific health endpoints
    for db_name in DB_CONFIGS.keys():
        endpoints[f"/{db_name}_health"] = f"Health check for {db_name} database"
    
    return jsonify({
        "service": "Oracle Database Monitor",
        "version": "1.0.0",
        "endpoints": endpoints
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Legacy health check endpoint - checks primary database for backward compatibility"""
    return check_database_health('primary')

def check_database_health(db_name):
    """Generic function to check health of a specific database"""
    start_time = time.time()
    
    try:
        connection = get_connection(db_name)
        
        with connection:
            # Execute a simple query to verify the connection is working
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
        
        # If we get here, the database is up
        response_time = round((time.time() - start_time) * 1000)
        config = DB_CONFIGS[db_name]
        
        return jsonify({
            "status": "UP",
            "database": f"{config['host']}:{config['port']}/{config['service_name']}",
            "database_name": db_name,
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        # If any error occurs, the database is considered down
        response_time = round((time.time() - start_time) * 1000)
        config = DB_CONFIGS[db_name]
        return jsonify({
            "status": "DOWN",
            "database": f"{config['host']}:{config['port']}/{config['service_name']}",
            "database_name": db_name,
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 503  # Service Unavailable status code

# Create dynamic routes for each database
for db_name in DB_CONFIGS.keys():
    route_path = f'/{db_name}_health'
    
    # This is a trick to create a closure with the current db_name
    def create_endpoint(db):
        def endpoint_function():
            return check_database_health(db)
        endpoint_function.__name__ = f"{db}_health_check"  # Unique function name required by Flask
        return endpoint_function
    
    # Register the route with Flask
    app.add_url_rule(route_path, f"{db_name}_health_check", create_endpoint(db_name), methods=['GET'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
