from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import oracledb
import os
import time
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

# Load environment variables from .env file if it exists
load_dotenv()

app = FastAPI(
    title="Oracle Database Monitor",
    description="A FastAPI application that monitors Oracle database for Dynatrace synthetic monitoring",
    version="1.0.0"
)

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

@app.get("/", response_class=JSONResponse)
async def index():
    """Root endpoint with basic information"""
    return {
        "service": "Oracle Database Monitor",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Basic database connectivity check",
            "/metrics": "Detailed database metrics",
            "/tablespace": "Tablespace usage information",
            "/sessions": "Active session information"
        }
    }

@app.get("/health", response_class=JSONResponse)
async def health_check():
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
        
        return {
            "status": "UP",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    except Exception as e:
        # If any error occurs, the database is considered down
        response_time = round((time.time() - start_time) * 1000)
        return JSONResponse(
            status_code=503,  # Service Unavailable
            content={
                "status": "DOWN",
                "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

@app.get("/metrics", response_class=JSONResponse)
async def database_metrics():
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
        
        return {
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": metrics
        }
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return JSONResponse(
            status_code=500,
            content={
                "status": "ERROR",
                "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

@app.get("/tablespace", response_class=JSONResponse)
async def tablespace_usage():
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
        
        return {
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "tablespaces": tablespaces
        }
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return JSONResponse(
            status_code=500,
            content={
                "status": "ERROR",
                "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

@app.get("/sessions", response_class=JSONResponse)
async def active_sessions():
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
        
        return {
            "status": "SUCCESS",
            "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
            "response_time_ms": response_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "active_sessions_count": len(sessions),
            "sessions": sessions
        }
    
    except Exception as e:
        response_time = round((time.time() - start_time) * 1000)
        return JSONResponse(
            status_code=500,
            content={
                "status": "ERROR",
                "database": f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['service_name']}",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
