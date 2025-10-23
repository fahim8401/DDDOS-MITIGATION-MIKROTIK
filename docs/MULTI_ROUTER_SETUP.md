# Multi-Router Setup Guide

This guide explains how to configure and use the multi-router DDoS monitoring system.

## Overview

The multi-router system allows you to monitor and manage DDoS attacks across multiple MikroTik routers from a single centralized dashboard.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Web Frontend  │ ───> │   Flask API      │ ───> │  MikroTik       │
│   (React)       │      │   (Backend)      │      │  Router 1       │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                 │                  ┌─────────────────┐
                                 ├────────────────> │  MikroTik       │
                                 │                  │  Router 2       │
                                 │                  └─────────────────┘
                                 ▼                  ┌─────────────────┐
                         ┌──────────────────┐      │  MikroTik       │
                         │  SQLite Database │<──── │  Router N       │
                         │  (Centralized)   │      └─────────────────┘
                         └──────────────────┘
```

## Database Schema

The system uses SQLAlchemy ORM with the following main tables:

- **routers**: Router configurations and connection details
- **events**: DDoS attack events with router associations
- **blocked_ips**: Blocked IP addresses per router
- **router_stats**: Router performance statistics
- **users**: User accounts with role-based access
- **settings**: System-wide configuration settings

## Initial Setup

### 1. Database Migration

Initialize the database with the required schema:

```bash
# Using SQLAlchemy ORM (recommended)
python3 scripts/migrate_db.py --orm --add-sample

# Or using SQL migration file
python3 scripts/migrate_db.py --migration migrations/001_initial.sql
```

This will create:
- All required tables
- Default system settings
- A sample router configuration (disabled by default)

### 2. Configure Routers

#### Option A: Using the API

```bash
# Add a new router
curl -X POST http://localhost:5000/api/routers \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Gateway",
    "host": "192.168.1.1",
    "port": 8728,
    "username": "admin",
    "password": "your-password",
    "enabled": true
  }'
```

#### Option B: Direct Database Insert

```python
from models import get_database, Router

db = get_database('sqlite:///ddos_events.db')
session = db.get_session()

router = Router(
    name='Main Gateway',
    host='192.168.1.1',
    port=8728,
    username='admin',
    password='your-password',
    use_ssl=False,
    enabled=True
)

session.add(router)
session.commit()
session.close()
```

### 3. Start the Services

#### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

This starts:
- **backend**: API server on port 5000
- **frontend**: Web interface on port 3000
- **monitor**: Multi-router monitoring service

#### Manual Start

```bash
# Terminal 1: Start the API
python3 api/app.py

# Terminal 2: Start the monitor
python3 mt_ddos_manager.py

# Terminal 3: Start the frontend (for development)
cd frontend
npm start
```

## API Endpoints

### Router Management

#### List All Routers
```bash
GET /api/routers
```

#### Get Router Details
```bash
GET /api/routers/{router_id}
```

#### Create Router
```bash
POST /api/routers
Content-Type: application/json

{
  "name": "Router Name",
  "host": "192.168.1.1",
  "port": 8728,
  "username": "admin",
  "password": "password",
  "use_ssl": false,
  "enabled": true
}
```

#### Update Router
```bash
PUT /api/routers/{router_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "enabled": false
}
```

#### Delete Router
```bash
DELETE /api/routers/{router_id}
```

#### Test Router Connection
```bash
POST /api/routers/{router_id}/test
```

#### Get Router Statistics
```bash
GET /api/routers/{router_id}/stats?hours=24
```

### Events

#### List Events (All Routers or Filtered)
```bash
GET /api/events?hours=24&router_id=1&severity=HIGH&limit=100
```

#### Get Event Statistics
```bash
GET /api/events/stats?hours=24&router_id=1
```

### Blocked IPs

#### List Blocked IPs
```bash
GET /api/blocked-ips?router_id=1
```

#### Block an IP
```bash
POST /api/blocked-ips
Content-Type: application/json

{
  "router_id": 1,
  "ip_address": "1.2.3.4",
  "reason": "Manual block",
  "duration": "1h"
}
```

#### Unblock an IP
```bash
DELETE /api/blocked-ips/{blocked_id}
```

### System Status

#### Health Check
```bash
GET /api/health
```

#### System Status
```bash
GET /api/status
```

#### Dashboard Summary
```bash
GET /api/dashboard/summary
```

## Configuration

### config.yml

The main configuration file supports multiple routers through the database. Key settings:

```yaml
# Database Configuration
database:
  path: "ddos_events.db"
  retention_days: 30
  auto_cleanup: true

# Detection Settings (applies to all routers)
detection:
  check_interval: 30
  packet_threshold: 10000
  auto_block_enabled: true
  block_duration: "1h"
  address_list_name: "ddos_blocklist"

# API Settings
api:
  enabled: true
  host: "0.0.0.0"
  port: 5000
  key: "changeme"  # Change this!
```

### Environment Variables

Override settings using environment variables:

```bash
export CONFIG_FILE=/path/to/config.yml
export API_KEY=your-secure-api-key
export DATABASE_PATH=/path/to/ddos_events.db
```

## Monitoring Multiple Routers

The system uses a multi-threaded approach where each router gets its own:

- **RouterClient**: Manages the connection to the router
- **MonitorWorker**: Runs monitoring loop in a separate thread
- Independent event detection and blocking actions

### How It Works

1. **Startup**: The `MultiRouterManager` loads all enabled routers from the database
2. **Thread Creation**: For each router, a `MonitorWorker` is created and started in its own thread
3. **Monitoring**: Each worker independently:
   - Connects to its assigned router
   - Analyzes traffic patterns
   - Detects DDoS attacks
   - Logs events to the centralized database
   - Automatically blocks malicious IPs (if enabled)
   - Collects router statistics
4. **Coordination**: The database serves as the central coordination point for all routers

## Best Practices

### Security

1. **API Keys**: Use strong, unique API keys
2. **Router Credentials**: Store credentials securely (consider environment variables)
3. **Network Isolation**: Run monitoring on a secure network
4. **Access Control**: Use role-based access for users
5. **SSL/TLS**: Enable SSL connections to routers when possible

### Performance

1. **Check Interval**: Balance between responsiveness and load (30-60 seconds recommended)
2. **Retention**: Configure appropriate event retention (30 days default)
3. **Database Cleanup**: Enable auto-cleanup to prevent database bloat
4. **Thread Count**: Monitor system resources when running many routers

### Reliability

1. **Connection Retry**: The system automatically retries failed connections
2. **Graceful Degradation**: Failed router connections don't affect other routers
3. **Health Monitoring**: Use the health check endpoint for monitoring
4. **Logging**: Monitor logs for connection issues and errors

## Troubleshooting

### Router Won't Connect

1. Check router credentials
2. Verify API is enabled on the router
3. Test network connectivity: `ping <router-ip>`
4. Check firewall rules
5. Use the connection test endpoint: `POST /api/routers/{id}/test`

### No Events Being Logged

1. Verify router is marked as 'connected' in the database
2. Check detection thresholds in config.yml
3. Review logs: `tail -f mt_ddos_manager.log`
4. Ensure auto-block is configured correctly
5. Verify firewall rules exist on the router

### Performance Issues

1. Reduce check_interval in config.yml
2. Lower packet_threshold for less sensitive detection
3. Enable database auto-cleanup
4. Monitor system resources (CPU, memory)
5. Consider running fewer routers per instance

### Database Issues

1. Check database file permissions
2. Verify SQLAlchemy version: `pip show SQLAlchemy`
3. Run migration again: `python3 scripts/migrate_db.py --orm`
4. Check database integrity: `sqlite3 ddos_events.db "PRAGMA integrity_check;"`

## Upgrading from Single Router

If you're upgrading from the single-router version:

1. **Backup**: Save your existing database and configuration
2. **Migrate**: Run the new migration to add router tables
3. **Import**: Convert your existing configuration to a router entry
4. **Test**: Verify the router connects before enabling monitoring
5. **Deploy**: Start the new multi-router manager

Example migration script:

```python
from models import get_database, Router
import yaml

# Load old config
with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Create router from old config
db = get_database('sqlite:///ddos_events.db')
session = db.get_session()

router = Router(
    name='Migrated Router',
    host=config['mikrotik']['host'],
    port=config['mikrotik']['port'],
    username=config['mikrotik']['username'],
    password=config['mikrotik']['password'],
    use_ssl=config['mikrotik'].get('use_ssl', False),
    enabled=True
)

session.add(router)
session.commit()
session.close()

print("Migration complete!")
```

## Examples

### Complete Setup Example

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python3 scripts/migrate_db.py --orm

# 3. Add routers via Python
python3 << EOF
from models import get_database, Router

db = get_database('sqlite:///ddos_events.db')
session = db.get_session()

# Add multiple routers
routers = [
    Router(name='Gateway 1', host='192.168.1.1', username='admin', password='pass1', enabled=True),
    Router(name='Gateway 2', host='192.168.2.1', username='admin', password='pass2', enabled=True),
    Router(name='Gateway 3', host='192.168.3.1', username='admin', password='pass3', enabled=True),
]

for router in routers:
    session.add(router)

session.commit()
session.close()
print("Added 3 routers")
EOF

# 4. Start services
docker-compose up -d

# 5. Check status
curl -H "X-API-Key: changeme" http://localhost:5000/api/status
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK/issues
- Documentation: See docs/ directory
- API Reference: See API.md
