#!/usr/bin/env python3
"""
Test script to verify Oracle database connection with timeout
"""
import oracledb
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def test_connection():
    """Test connection to Oracle database with timeout"""
    print("Testing connection to Oracle database with timeout...")
    
    # Get connection parameters from environment variables
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', 1521))
    service_name = os.environ.get('DB_SERVICE_NAME', 'ORCLPDB1')
    user = os.environ.get('DB_USER', 'system')
    password = os.environ.get('DB_PASSWORD', 'oracle')
    
    print(f"Connection parameters:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Service Name: {service_name}")
    print(f"  User: {user}")
    print(f"  Password: {'*' * len(password)}")
    
    try:
        # Create the connection string
        dsn = oracledb.makedsn(
            host=host,
            port=port,
            service_name=service_name
        )
        
        print(f"DSN: {dsn}")
        print("Attempting connection with 5 second timeout...")
        
        start_time = time.time()
        
        # Attempt to connect to the database with timeout
        connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn,
            timeout=5  # 5 second timeout for connection attempt
        )
        
        connection_time = time.time() - start_time
        print(f"Connection established in {connection_time:.2f} seconds")
        
        with connection:
            # Execute a simple query to verify the connection is working
            with connection.cursor() as cursor:
                cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
                version = cursor.fetchone()
                
                if version:
                    print(f"\nConnection successful!")
                    print(f"Oracle version: {version[0]}")
                else:
                    print("\nConnection successful, but couldn't retrieve version information.")
            
            print("\nConnection will be automatically closed after this test")
        
        print("Connection closed")
        return True
    
    except Exception as e:
        print(f"\nConnection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
