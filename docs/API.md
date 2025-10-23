# API Documentation

This document describes the RESTful API endpoints provided by the MikroTik DDoS Monitor application.

## Base URL

```
http://localhost:5000/api
```

## Authentication

All endpoints (except `/health`) require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/status
```

## Endpoints

### Health Check

Check the health status of the application.

**Endpoint:** `GET /api/health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "router": "connected",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Status

Get current system status.

**Endpoint:** `GET /api/status`

**Authentication:** Required

**Response:**
```json
{
  "status": "operational",
  "router_connected": true,
  "recent_events_count": 5,
  "blocked_ips_count": 3,
  "monitoring_active": true,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Events

Retrieve DDoS events with optional filtering.

**Endpoint:** `GET /api/events`

**Authentication:** Required

**Query Parameters:**
- `hours` (optional): Number of hours to look back (default: 24)
- `severity` (optional): Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `limit` (optional): Maximum number of events to return (default: 100)

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:5000/api/events?hours=24&severity=HIGH&limit=50"
```

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "attack_type": "SYN Flood",
      "source_ip": "1.2.3.4",
      "target_ip": "192.168.88.1",
      "packet_rate": 15000,
      "severity": "HIGH",
      "action_taken": "Blocked"
    }
  ],
  "total": 1,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Event Statistics

Get statistical summary of events.

**Endpoint:** `GET /api/events/stats`

**Authentication:** Required

**Query Parameters:**
- `hours` (optional): Number of hours to look back (default: 24)

**Response:**
```json
{
  "total_events": 10,
  "by_severity": {
    "CRITICAL": 2,
    "HIGH": 3,
    "MEDIUM": 4,
    "LOW": 1
  },
  "by_type": {
    "SYN Flood": 5,
    "UDP Flood": 3,
    "ICMP Flood": 2
  },
  "unique_sources": 5,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Blocked IPs

List currently blocked IP addresses.

**Endpoint:** `GET /api/blocked-ips`

**Authentication:** Required

**Response:**
```json
{
  "blocked_ips": [
    {
      "address": "1.2.3.4",
      "comment": "DDoS Attack - 2024-01-01T12:00:00",
      "timeout": "1h"
    }
  ],
  "total": 1,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Block IP Address

Manually block an IP address.

**Endpoint:** `POST /api/blocked-ips`

**Authentication:** Required

**Request Body:**
```json
{
  "ip_address": "1.2.3.4",
  "reason": "Manual block - suspicious activity"
}
```

**Response:**
```json
{
  "success": true,
  "message": "IP 1.2.3.4 blocked successfully",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Error Response:**
```json
{
  "error": "IP address is required"
}
```

### Unblock IP Address

Remove an IP address from the blocklist.

**Endpoint:** `DELETE /api/blocked-ips/{ip_address}`

**Authentication:** Required

**Example:**
```bash
curl -X DELETE -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/blocked-ips/1.2.3.4
```

**Response:**
```json
{
  "success": true,
  "message": "IP 1.2.3.4 unblocked successfully",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Configuration

Get current configuration (sensitive data redacted).

**Endpoint:** `GET /api/config`

**Authentication:** Required

**Response:**
```json
{
  "detection": {
    "check_interval": 30,
    "packet_threshold": 10000,
    "auto_block_enabled": true
  },
  "monitoring": {
    "check_interval": 30,
    "auto_block_enabled": true
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Router Information

Get information about the connected MikroTik router.

**Endpoint:** `GET /api/router/info`

**Authentication:** Required

**Response:**
```json
{
  "platform": "MikroTik",
  "board_name": "RB4011iGS+",
  "version": "7.12.1",
  "uptime": "2w3d4h5m",
  "cpu_load": 15,
  "free_memory": 512000000,
  "total_memory": 1073741824,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Get Dashboard Summary

Get comprehensive dashboard data.

**Endpoint:** `GET /api/dashboard/summary`

**Authentication:** Required

**Response:**
```json
{
  "total_events_24h": 10,
  "critical_events": 2,
  "high_events": 3,
  "blocked_ips_count": 5,
  "router_connected": true,
  "monitoring_active": true,
  "recent_events": [
    {
      "timestamp": "2024-01-01T12:00:00",
      "attack_type": "SYN Flood",
      "source_ip": "1.2.3.4",
      "severity": "HIGH"
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "error": "Invalid or missing API key"
}
```

### 404 Not Found
```json
{
  "error": "Endpoint not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Service unavailable"
}
```

## Rate Limiting

The API implements rate limiting (configurable in `config.yml`):
- Default: 100 requests per minute per IP address
- Exceeded limit returns HTTP 429 (Too Many Requests)

## Security Considerations

1. **Always use HTTPS in production** to protect API keys
2. **Keep API keys secure** - don't commit them to version control
3. **Rotate API keys regularly**
4. **Use IP whitelisting** when possible
5. **Monitor API access logs** for suspicious activity

## Example Usage

### Python

```python
import requests

API_URL = "http://localhost:5000/api"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get status
response = requests.get(f"{API_URL}/status", headers=headers)
print(response.json())

# Block an IP
data = {
    "ip_address": "1.2.3.4",
    "reason": "Suspicious activity"
}
response = requests.post(f"{API_URL}/blocked-ips", json=data, headers=headers)
print(response.json())
```

### JavaScript

```javascript
const API_URL = 'http://localhost:5000/api';
const API_KEY = 'your-api-key';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Get events
fetch(`${API_URL}/events?hours=24`, { headers })
  .then(response => response.json())
  .then(data => console.log(data));

// Block an IP
fetch(`${API_URL}/blocked-ips`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    ip_address: '1.2.3.4',
    reason: 'Suspicious activity'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL

```bash
# Get status
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/status

# Get events
curl -H "X-API-Key: your-api-key" \
  "http://localhost:5000/api/events?hours=24&severity=HIGH"

# Block IP
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"ip_address":"1.2.3.4","reason":"Manual block"}' \
  http://localhost:5000/api/blocked-ips

# Unblock IP
curl -X DELETE \
  -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/blocked-ips/1.2.3.4
```

## Webhooks (Future Feature)

Future versions will support webhook notifications for events. Configuration will be available in `config.yml`.
