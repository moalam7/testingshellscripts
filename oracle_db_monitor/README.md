# Oracle Database Monitor for Dynatrace

This is a simple Flask API that connects to an Oracle database and provides monitoring endpoints that can be used with Dynatrace synthetic monitoring.

## Features

- Basic health check endpoint to verify database connectivity
- Detailed metrics endpoint for database version, instance status, and uptime
- Tablespace usage information
- Active session monitoring
- Custom query endpoint (read-only)

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
python app.py
```

The API will be available at http://localhost:5000

### Running with Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

### GET /

Returns basic information about available endpoints.

### GET /health

Basic health check endpoint that verifies database connectivity.

Example response:
```json
{
  "status": "UP",
  "database": "localhost:1521/ORCLPDB1",
  "response_time_ms": 25,
  "timestamp": "2025-04-21T12:57:00.123456"
}
```

### GET /metrics

Returns detailed database metrics including version, instance status, and uptime.

### GET /tablespace

Returns information about tablespace usage.

### GET /sessions

Returns information about active database sessions.

### POST /custom

Runs a custom SQL query (read-only).

Request body:
```json
{
  "query": "SELECT * FROM v$version"
}
```

## Integrating with Dynatrace

To monitor your Oracle database with Dynatrace synthetic monitoring:

1. Deploy this API on a server that can access your Oracle database
2. Create a synthetic HTTP monitor in Dynatrace that calls the `/health` endpoint
3. Set up alerts based on the response status and response time

You can also create additional synthetic monitors for the other endpoints to monitor specific aspects of your database.

## Security Considerations

- This API should be deployed behind a secure proxy or firewall
- Use HTTPS in production
- Consider implementing authentication for the API
- The custom query endpoint only allows SELECT queries, but additional security measures may be needed
