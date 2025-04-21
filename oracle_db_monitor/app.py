from flask import Flask, jsonify, request
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

def get_connection():
    """Create and return a database connection"""
    dsn = oracledb.makedsn(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        service_name=DB_CONFIG['service_name']
    )
    
    connection = oracledb.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        dsn=dsn
    )
    return connection

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with basic information"""
    return jsonify({
        "service": "Oracle Database Monitor",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Basic database connectivity check",
            "/metrics": "Detailed database metrics",
            "/tablespace": "Tablespace usage information",
            "/sessions": "Active session information",
            "/custom": "Run custom SQL query (POST with 'query' parameter)"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Check if Oracle database is up and return status for Dynatrace to monitor"""
    start_time = time.time()
    
    try:
        connection = get_connection()
        
        with connection:
            # Execute a simple query to verify the connection is working
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
        
        # If we get here, the database is up
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "UP",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        # If any error occurs, the database is considered down
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "DOWN",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 503  # Service Unavailable status code

@app.route('/metrics', methods=['GET'])
def database_metrics():
    """Get detailed database metrics"""
    start_time = time.time()
    
    try:
        connection = get_connection()
        metrics = {}
        
        with connection:
            # Get database version
            with connection.cursor() as cursor:
                cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
                version = cursor.fetchone()
                metrics["version"] = version[0] if version else "Unknown"
            
            # Get instance status
            with connection.cursor() as cursor:
                cursor.execute("SELECT INSTANCE_NAME, STATUS, DATABASE_STATUS FROM V$INSTANCE")
                instance = cursor.fetchone()
                if instance:
                    metrics["instance_name"] = instance[0]
                    metrics["instance_status"] = instance[1]
                    metrics["database_status"] = instance[2]
            
            # Get database uptime
            with connection.cursor() as cursor:
                cursor.execute("SELECT STARTUP_TIME FROM V$INSTANCE")
                startup = cursor.fetchone()
                if startup:
                    metrics["startup_time"] = startup[0].strftime("%Y-%m-%d %H:%M:%S")
        
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": metrics
        })
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "ERROR",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/tablespace', methods=['GET'])
def tablespace_usage():
    """Get tablespace usage information"""
    start_time = time.time()
    
    try:
        connection = get_connection()
        tablespaces = []
        
        with connection:
            query = """
            SELECT 
                df.tablespace_name "Tablespace",
                df.bytes / (1024 * 1024) "Size (MB)",
                SUM(fs.bytes) / (1024 * 1024) "Free (MB)",
                df.bytes / (1024 * 1024) - SUM(fs.bytes) / (1024 * 1024) "Used (MB)",
                ROUND((df.bytes - SUM(fs.bytes)) / df.bytes * 100, 2) "Used %"
            FROM 
                dba_free_space fs,
                (SELECT tablespace_name, SUM(bytes) bytes FROM dba_data_files GROUP BY tablespace_name) df
            WHERE 
                fs.tablespace_name (+) = df.tablespace_name
            GROUP BY 
                df.tablespace_name, df.bytes
            ORDER BY 
                df.tablespace_name
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                
                for row in cursor:
                    tablespace = dict(zip(columns, row))
                    tablespaces.append(tablespace)
        
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "tablespaces": tablespaces
        })
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "ERROR",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/sessions', methods=['GET'])
def active_sessions():
    """Get active session information"""
    start_time = time.time()
    
    try:
        connection = get_connection()
        sessions = []
        
        with connection:
            query = """
            SELECT 
                s.sid,
                s.serial#,
                s.username,
                s.status,
                s.machine,
                s.program,
                s.logon_time,
                s.last_call_et "Seconds Since Last Call"
            FROM 
                v$session s
            WHERE 
                s.type = 'USER'
            ORDER BY 
                s.status, s.last_call_et DESC
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                
                for row in cursor:
                    # Convert datetime objects to strings for JSON serialization
                    row_data = list(row)
                    for i, val in enumerate(row_data):
                        if isinstance(val, datetime.datetime):
                            row_data[i] = val.isoformat()
                    
                    session = dict(zip(columns, row_data))
                    sessions.append(session)
        
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "active_sessions_count": len(sessions),
            "sessions": sessions
        })
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "ERROR",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

@app.route('/custom', methods=['POST'])
def custom_query():
    """Run a custom SQL query (read-only)"""
    start_time = time.time()
    
    # Get query from request
    query = request.json.get('query')
    if not query:
        return jsonify({
            "status": "ERROR",
            "error": "No query provided",
            "timestamp": datetime.datetime.now().isoformat()
        }), 400
    
    # Check if query is read-only (simple check, not foolproof)
    query_upper = query.upper()
    if any(keyword in query_upper for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE']):
        return jsonify({
            "status": "ERROR",
            "error": "Only SELECT queries are allowed",
            "timestamp": datetime.datetime.now().isoformat()
        }), 403
    
    try:
        connection = get_connection()
        results = []
        
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                
                for row in cursor:
                    # Convert datetime objects to strings for JSON serialization
                    row_data = list(row)
                    for i, val in enumerate(row_data):
                        if isinstance(val, datetime.datetime):
                            row_data[i] = val.isoformat()
                    
                    result = dict(zip(columns, row_data))
                    results.append(result)
        
        response_time = round((time.time() - start_time) * 1000)
        
        return jsonify({
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "row_count": len(results),
            "results": results
        })
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return jsonify({
            "status": "ERROR",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "error": str(e),
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
