# Oracle Database Monitor for Dynatrace (Simplified Flask Version)

This is a simplified Flask application that connects to an Oracle database and provides a health check endpoint that can be used with Dynatrace synthetic monitoring.

## Features

- Single health check endpoint to verify database connectivity
- Connection timeout mechanism to prevent hanging connections
- Auto-refresh functionality with configurable intervals
- Connections are only established when the endpoint is accessed
- Connections are closed immediately after use
- HTML interface for human monitoring and JSON response for API clients

## Requirements

- Python 3.6+
- Oracle client libraries (if using thick mode)
- Oracle database access

## Installation

1. Clone this repository or copy the files to your server
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the `.env.example` template:

```bash
cp .env.example .env
```

4. Edit the `.env` file with your Oracle database connection details

## Usage

### Running the API locally

```bash
./run.sh
```

The health check page will be available at http://localhost:5000/health

### Running with Gunicorn (Production)

```bash
./deploy.sh
```

## Health Check Endpoint

### GET /health

Basic health check endpoint that verifies database connectivity.

#### HTML Response (default)

When accessed in a browser, this endpoint returns an HTML page with:
- Database connection status
- Response time
- Auto-refresh controls (configurable intervals)
- Last check timestamp

The page automatically refreshes at the specified interval (default: 5 minutes).

#### JSON Response

When accessed with `Accept: application/json` header or `?format=json` query parameter:

```json
{
  "status": "UP",
  "database": "localhost:1521/ORCLPDB1",
  "response_time_ms": 25,
  "timestamp": "2025-04-21T12:57:00.123456"
}
```

## Connection Management

- Database connections are only established when the health check endpoint is accessed
- Each connection has a 5-second timeout to prevent hanging connections
- Connections are automatically closed after the health check is completed
- No persistent connections are maintained between checks

## Integrating with Dynatrace

To monitor your Oracle database with Dynatrace synthetic monitoring:

1. Deploy this API on a server that can access your Oracle database
2. Create a synthetic HTTP monitor in Dynatrace that calls the `/health` endpoint with the `Accept: application/json` header
3. Set up alerts based on the response status and response time

## Security Considerations

- This API should be deployed behind a secure proxy or firewall
- Use HTTPS in production
- Consider implementing authentication for the API
