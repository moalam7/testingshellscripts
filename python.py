import oracledb
from flask import Flask, Response
import time

app = Flask(__name__)

# Oracle connection details
DB_USER = "scott"  # Replace with your username
DB_PASSWORD = "tiger"  # Replace with your password
DB_HOST = "localhost"  # Replace with your host
DB_PORT = "1521"  # Replace with your port
DB_SERVICE = "orclpdb"  # Replace with your service name or SID

# DSN for oracledb
DSN = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

@app.route("/health")
def health_check():
    start_time = time.time_ns()
    status = "UP"
    error = ""
    
    try:
        # Connect to Oracle
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DSN) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    status = "UP"
                else:
                    status = "DOWN"
                    error = "Query did not return expected result"
    except oracledb.Error as e:
        status = "DOWN"
        error = str(e)

    # Calculate response time in milliseconds
    response_time = (time.time_ns() - start_time) // 1_000_000

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Oracle Database Health Check</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            .status-up {{ color: green; font-size: 24px; }}
            .status-down {{ color: red; font-size: 24px; }}
        </style>
    </head>
    <body>
        <h1>Oracle Database Health Check</h1>
        <p>Database: {DB_HOST}</p>
        <p>Service Name: {DB_SERVICE}</p>
        <p class="status-{status.lower()}">Status: {status}</p>
        <p>Response Time: {response_time} ms</p>
        {f'<p>Error: {error}</p>' if error else ''}
    </body>
    </html>
    """
    
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
