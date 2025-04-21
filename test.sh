#!/bin/bash

# Database connection details
DB_USER="scott"  # Replace with your Oracle username
DB_PASSWORD="tiger"  # Replace with your Oracle password
DB_HOST="localhost"  # Replace with your database host
DB_PORT="1521"  # Replace with your database port
DB_SERVICE="orclpdb"  # Replace with your service name or SID

# Output HTML file
HTML_FILE="/var/www/html/health.html"  # Adjust path based on your HTTP server

# Start time for response time calculation
START_TIME=$(date +%s%N)

# Test database connection using sqlplus
SQLPLUS_OUTPUT=$(sqlplus -S /nolog <<EOF
  CONNECT ${DB_USER}/${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_SERVICE}
  SELECT 1 FROM dual;
  EXIT;
EOF
)

# Check if sqlplus command was successful
if echo "$SQLPLUS_OUTPUT" | grep -q "1"; then
  STATUS="UP"
  ERROR=""
else
  STATUS="DOWN"
  ERROR=$(echo "$SQLPLUS_OUTPUT" | grep "ORA-" || echo "Unknown error")
fi

# Calculate response time in milliseconds
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

# Generate HTML content
cat > "$HTML_FILE" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oracle Database Health Check</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .status-up { color: green; font-size: 24px; }
        .status-down { color: red; font-size: 24px; }
    </style>
</head>
<body>
    <h1>Oracle Database Health Check</h1>
    <p>Database: ${DB_HOST}</p>
    <p>Service Name: ${DB_SERVICE}</p>
    <p class="status-${STATUS,,}">Status: ${STATUS}</p>
    <p>Response Time: ${RESPONSE_TIME} ms</p>
    ${ERROR:+<p>Error: ${ERROR}</p>}
</body>
</html>
EOF

# Ensure the HTML file has proper permissions
chmod 644 "$HTML_FILE"
