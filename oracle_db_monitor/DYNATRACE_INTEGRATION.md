# Dynatrace Integration Guide for Oracle Database Monitor

This guide explains how to integrate the Oracle Database Monitor API with Dynatrace synthetic monitoring to monitor your Oracle databases.

## Prerequisites

- Oracle Database Monitor API deployed and accessible via HTTP/HTTPS
- Dynatrace account with synthetic monitoring capabilities
- Appropriate permissions to create synthetic monitors in Dynatrace

## Setting Up Synthetic Monitoring in Dynatrace

### 1. Basic Health Check Monitor

This monitor will periodically check if your Oracle database is up and running.

1. Log in to your Dynatrace environment
2. Navigate to **Synthetic** > **Create a synthetic monitor** > **HTTP monitor**
3. Configure the monitor:
   - **Name**: Oracle Database Health Check
   - **URL**: `http://your-api-url/health` (replace with your actual API URL)
   - **Frequency**: Choose how often to run the check (e.g., 5 minutes)
   - **Locations**: Select the locations to run the monitor from
4. Add validation rules:
   - Add a rule to check for HTTP status code 200
   - Add a rule to validate JSON response contains `"status": "UP"`
5. Set up alerting:
   - Configure alert conditions based on your requirements
   - Set up notification integrations if needed
6. Save and activate the monitor

### 2. Tablespace Usage Monitor

This monitor will track your Oracle database tablespace usage.

1. Navigate to **Synthetic** > **Create a synthetic monitor** > **HTTP monitor**
2. Configure the monitor:
   - **Name**: Oracle Tablespace Usage Monitor
   - **URL**: `http://your-api-url/tablespace` (replace with your actual API URL)
   - **Frequency**: Choose how often to run the check (e.g., 1 hour)
   - **Locations**: Select the locations to run the monitor from
3. Add validation rules:
   - Add a rule to check for HTTP status code 200
   - Add a rule to validate JSON response contains `"status": "SUCCESS"`
4. Add JavaScript to extract and evaluate tablespace usage:
   ```javascript
   // Extract tablespace usage information
   var response = JSON.parse(responseBody);
   var tablespaces = response.tablespaces;
   
   // Check if any tablespace is over 90% full
   var criticalTablespaces = [];
   for (var i = 0; i < tablespaces.length; i++) {
     var tablespace = tablespaces[i];
     if (tablespace["Used %"] > 90) {
       criticalTablespaces.push(tablespace["Tablespace"] + " (" + tablespace["Used %"] + "%)");
     }
   }
   
   // Fail the check if any tablespace is critical
   if (criticalTablespaces.length > 0) {
     throw new Error("Critical tablespace usage: " + criticalTablespaces.join(", "));
   }
   ```
5. Set up alerting based on your requirements
6. Save and activate the monitor

### 3. Database Metrics Monitor

This monitor will track general database metrics.

1. Navigate to **Synthetic** > **Create a synthetic monitor** > **HTTP monitor**
2. Configure the monitor:
   - **Name**: Oracle Database Metrics Monitor
   - **URL**: `http://your-api-url/metrics` (replace with your actual API URL)
   - **Frequency**: Choose how often to run the check (e.g., 15 minutes)
   - **Locations**: Select the locations to run the monitor from
3. Add validation rules:
   - Add a rule to check for HTTP status code 200
   - Add a rule to validate JSON response contains `"status": "SUCCESS"`
4. Add JavaScript to extract and evaluate metrics:
   ```javascript
   // Extract database metrics
   var response = JSON.parse(responseBody);
   var metrics = response.metrics;
   
   // Check database status
   if (metrics.database_status !== "ACTIVE" || metrics.instance_status !== "OPEN") {
     throw new Error("Database is not in normal operating state: " + 
                    "Instance status: " + metrics.instance_status + 
                    ", Database status: " + metrics.database_status);
   }
   
   // Record response time as a custom metric
   var responseTime = response.response_time_ms;
   DTrum.addMetric("oracle_response_time", responseTime);
   ```
5. Set up alerting based on your requirements
6. Save and activate the monitor

### 4. Active Sessions Monitor

This monitor will track active sessions in your database.

1. Navigate to **Synthetic** > **Create a synthetic monitor** > **HTTP monitor**
2. Configure the monitor:
   - **Name**: Oracle Active Sessions Monitor
   - **URL**: `http://your-api-url/sessions` (replace with your actual API URL)
   - **Frequency**: Choose how often to run the check (e.g., 10 minutes)
   - **Locations**: Select the locations to run the monitor from
3. Add validation rules:
   - Add a rule to check for HTTP status code 200
   - Add a rule to validate JSON response contains `"status": "SUCCESS"`
4. Add JavaScript to extract and evaluate session information:
   ```javascript
   // Extract session information
   var response = JSON.parse(responseBody);
   var sessionCount = response.active_sessions_count;
   
   // Record session count as a custom metric
   DTrum.addMetric("oracle_active_sessions", sessionCount);
   
   // Alert if session count exceeds threshold
   var threshold = 100; // Adjust based on your environment
   if (sessionCount > threshold) {
     throw new Error("High number of active sessions: " + sessionCount + " (threshold: " + threshold + ")");
   }
   ```
5. Set up alerting based on your requirements
6. Save and activate the monitor

## Setting Up Custom Dashboards

You can create custom dashboards in Dynatrace to visualize the data collected by your synthetic monitors:

1. Navigate to **Dashboards** > **Create dashboard**
2. Add tiles for your synthetic monitors:
   - Add a **Synthetic monitor status** tile for each monitor
   - Add **Custom chart** tiles to visualize metrics like response time and active sessions
3. Arrange and customize the dashboard as needed

## Alerting and Notifications

Configure alerting policies to be notified when issues are detected:

1. Navigate to **Settings** > **Alerting** > **Problem detection and alerting**
2. Configure alerting profiles based on your requirements
3. Set up notification integrations (email, Slack, PagerDuty, etc.)
4. Associate your synthetic monitors with the appropriate alerting profiles

## Troubleshooting

If you encounter issues with your synthetic monitors:

1. Check the API logs for errors
2. Verify that the API is accessible from the Dynatrace synthetic monitoring locations
3. Ensure that your Oracle database connection parameters are correct
4. Check for any network or firewall issues that might be blocking the connections

## Security Considerations

- Use HTTPS for your API to encrypt the data in transit
- Implement authentication for your API to prevent unauthorized access
- Consider using a dedicated database user with read-only permissions for monitoring
- Regularly review and update your database credentials
- Implement IP restrictions to only allow connections from trusted sources

## Advanced Configuration

For more advanced monitoring scenarios, you can use the `/custom` endpoint to run specific SQL queries that are relevant to your application. For example:

```json
{
  "query": "SELECT COUNT(*) as transaction_count FROM transactions WHERE status = 'PENDING' AND created_at > SYSDATE - 1/24"
}
```

This would allow you to monitor application-specific metrics like the number of pending transactions in the last hour.
