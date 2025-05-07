from flask import Flask, jsonify
import oracledb
import os
import time
import datetime

app = Flask(__name__)

# Define the required database names
DATABASE_NAMES = ["dev", "sit", "uat", "reg", "nht", "ftp"]

# Build the database configurations dictionary dynamically
DB_CONFIGS = {}
for db_name in DATABASE_NAMES:
    upper_db_name = db_name.upper()
    DB_CONFIGS[db_name] = {
        "host": os.environ.get(f"{upper_db_name}_DB_HOST", "localhost"),
        "port": int(os.environ.get(f"{upper_db_name}_DB_PORT", 1521)),
        "service_name": os.environ.get(f"{upper_db_name}_DB_SERVICE_NAME", f"ORCLPDB_{db_name}"), # Example default
        "user": os.environ.get(f"{upper_db_name}_DB_USER", "system"),
        "password": os.environ.get(f"{upper_db_name}_DB_PASSWORD", "oracle"),
    }

def get_connection(db_name):
    """Create and return a database connection for the specified database"""
    if db_name not in DB_CONFIGS:
        raise ValueError(f"Unknown database: {db_name}")
    
    config = DB_CONFIGS[db_name]
    dsn = oracledb.makedsn(
        host=config["host"],
        port=config["port"],
        service_name=config["service_name"]
    )
    
    connection = None # Initialize connection to None
    try:
        connection = oracledb.connect(
            user=config["user"],
            password=config["password"],
            dsn=dsn
        )
        return connection
    except oracledb.DatabaseError as e:
        # If connection fails, re-raise the specific error for the health check to catch
        raise e
    except Exception as e:
        # Catch other potential errors during connection setup
        raise ValueError(f"Error creating DSN or connecting for {db_name}: {e}")

@app.route("/", methods=["GET"])
def index():
    """Root endpoint with basic information and list of health endpoints"""
    endpoints = {}
    # Add all database-specific health endpoints
    for db_name in DB_CONFIGS.keys():
        endpoints[f"/{db_name}_health"] = f"Health check for {db_name} database"
    
    return jsonify({
        "service": "Oracle Database Monitor",
        "version": "1.1.0", # Updated version
        "endpoints": endpoints
    })

def check_database_health(db_name):
    """Generic function to check health of a specific database"""
    start_time = time.time()
    config = DB_CONFIGS[db_name]
    db_identifier = f"{config['host']}:{config['port']}/{config['service_name']}"
    
    connection = None # Ensure connection is defined in the scope
    try:
        connection = get_connection(db_name)
        
        with connection:
            # Execute a simple query to verify the connection is working
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
        
        # If we get here, the database is up
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "UP",
            "database": db_identifier,
            "database_name": db_name,
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        # If any error occurs during connection or query, the database is considered down
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "DOWN",
            "database": db_identifier,
            "database_name": db_name,
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 503  # Service Unavailable status code

# Create dynamic routes for each database
for db_name in DB_CONFIGS.keys():
    route_path = f"/{db_name}_health"
    endpoint_name = f"{db_name}_health_check"
    
    # Use a default argument in lambda to capture the current db_name correctly
    app.add_url_rule(route_path, endpoint_name, lambda db=db_name: check_database_health(db), methods=["GET"])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
