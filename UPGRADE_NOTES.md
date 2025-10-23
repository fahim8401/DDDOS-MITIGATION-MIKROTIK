# Multi-Router Upgrade Notes

## What's New

This update transforms the single-router DDoS monitoring system into a **multi-router centralized platform**.

### Key Changes

1. **Database**: Now uses SQLAlchemy ORM with support for multiple routers
2. **Manager**: New `mt_ddos_manager.py` replaces single-router monitor
3. **API**: Enhanced with full router CRUD operations
4. **Architecture**: Each router monitored independently in parallel

### Quick Start

```bash
# 1. Install updated dependencies
pip install -r requirements.txt

# 2. Initialize new database (existing data preserved)
python3 scripts/migrate_db.py --orm --add-sample

# 3. Add your routers via API
curl -X POST http://localhost:5000/api/routers \
  -H "X-API-Key: changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Router",
    "host": "192.168.88.1",
    "port": 8728,
    "username": "admin",
    "password": "your-password",
    "enabled": true
  }'

# 4. Start services
docker-compose up -d
```

### Migration from Single Router

If you have existing configuration in `config.yml`:

```python
# Convert to multi-router (one-time migration)
from models import get_database, Router
import yaml

with open('config.yml') as f:
    config = yaml.safe_load(f)

db = get_database('sqlite:///ddos_events.db')
session = db.get_session()

router = Router(
    name='Migrated Router',
    host=config['mikrotik']['host'],
    port=config['mikrotik']['port'],
    username=config['mikrotik']['username'],
    password=config['mikrotik']['password'],
    enabled=True
)

session.add(router)
session.commit()
session.close()
```

### Breaking Changes

- **None**: Old single-router `mt_ddos_monitor.py` still works
- Database schema extended but backwards compatible
- All existing API endpoints work with new features added

### New API Endpoints

```bash
# Router Management
GET    /api/routers              # List all routers
POST   /api/routers              # Create router
GET    /api/routers/{id}         # Get router details
PUT    /api/routers/{id}         # Update router
DELETE /api/routers/{id}         # Delete router
POST   /api/routers/{id}/test    # Test connection
GET    /api/routers/{id}/stats   # Get statistics

# Enhanced Endpoints (now support router_id parameter)
GET /api/events?router_id=1
GET /api/blocked-ips?router_id=1
```

### Documentation

- **Setup Guide**: [docs/MULTI_ROUTER_SETUP.md](docs/MULTI_ROUTER_SETUP.md)
- **API Reference**: Check endpoint comments in `api/app.py`
- **Database Schema**: See `migrations/001_initial.sql`

### Testing

All tests pass (22/22):
```bash
pytest tests/ -v
```

### Security Updates

- Werkzeug upgraded from 3.0.1 to 3.0.3 (fixes CVE-2023-25577)
- CodeQL scan: 0 vulnerabilities

### Support

For issues or questions:
- GitHub Issues: https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK/issues
- Documentation: See `docs/` directory

---

**Note**: This is a major enhancement but maintains full backwards compatibility with existing single-router setups.
