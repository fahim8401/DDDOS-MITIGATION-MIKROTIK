# MikroTik DDoS Monitor & Auto-Actuator

A comprehensive Python-based application for real-time DDoS attack monitoring and automated mitigation on MikroTik routers using RouterOS API.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![RouterOS](https://img.shields.io/badge/RouterOS-7.x-orange.svg)

## 🎯 Features

### Multi-Router Support ⭐ NEW
- **Centralized Management**: Monitor multiple MikroTik routers from a single dashboard
- **Independent Monitoring**: Each router monitored in parallel with dedicated threads
- **Unified Database**: Centralized SQLite database with SQLAlchemy ORM
- **Per-Router Configuration**: Individual settings and credentials for each router
- **Router Management API**: Full CRUD operations for router configurations

### Real-time Monitoring
- **Continuous Traffic Analysis**: Monitor network traffic patterns in real-time
- **Multiple Attack Detection**: Identify SYN floods, UDP floods, ICMP floods, and connection flooding
- **Configurable Thresholds**: Customize detection sensitivity based on your network
- **Event Logging**: SQLite database for historical attack data and analysis

### Automated Mitigation
- **Auto-blocking**: Automatically block malicious IPs based on severity
- **Address List Management**: Integrate with MikroTik's firewall address lists
- **Temporary Bans**: Configurable timeout periods for blocked IPs
- **Whitelist Support**: Protect trusted IPs from being blocked

### Web Dashboard
- **Real-time Statistics**: View current attack status and trends
- **Event History**: Browse detailed attack logs with filtering
- **IP Management**: Manually block/unblock IP addresses
- **Router Status**: Monitor router connection and resource usage
- **Multi-Router View**: See events and statistics across all routers

### RESTful API
- **Complete API Coverage**: Manage all features programmatically
- **API Key Authentication**: Secure access to monitoring endpoints
- **JSON Responses**: Easy integration with other tools
- **Health Checks**: Monitor application status
- **Router Management**: Create, update, delete, and test router connections

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Web Frontend  │ ───> │   Flask API      │ ───> │  MikroTik       │
│   (React)       │      │   (SQLAlchemy)   │      │  Router 1       │
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
                                 ▲
                                 │
                         ┌──────────────────┐
                         │  Monitor Manager │
                         │  (Multi-Router)  │
                         └──────────────────┘
```

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **MikroTik Router**: RouterOS 7.x with API enabled
- **Docker** (optional): For containerized deployment
- **Node.js**: 18+ (for frontend development)

## 🚀 Quick Start

> **Note**: This system now supports multiple routers! See [docs/MULTI_ROUTER_SETUP.md](docs/MULTI_ROUTER_SETUP.md) for complete multi-router setup guide.

### 1. Clone the Repository

```bash
git clone https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK.git
cd DDDOS-MITIGATION-MIKROTIK
```

### 2. Configure MikroTik Router

Import the RouterOS configuration:

```bash
# Copy scripts/mikrotik-scripts.rsc to your router
# Then import it via RouterOS terminal:
/import mikrotik-scripts.rsc
```

This will configure:
- Firewall rules for DDoS protection
- Address lists for blocking/whitelisting
- Connection tracking settings
- Rate limiting rules

### 3. Configure Application

Edit `config.yml` with your router credentials:

```yaml
mikrotik:
  host: "192.168.88.1"      # Your router IP
  username: "admin"          # RouterOS username
  password: "your-password"  # RouterOS password
  port: 8728
```

### 4. Install Dependencies and Initialize Database

```bash
pip install -r requirements.txt

# Initialize the multi-router database
python3 scripts/migrate_db.py --orm --add-sample
```

### 5. Run the Application

#### Option A: Manual Start

```bash
# Start the multi-router monitor
python mt_ddos_manager.py

# In another terminal, start the API
python api/app.py
```

#### Option B: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Access the web dashboard at: `http://localhost:3000`

## 📖 Usage

### Command Line

Run the monitor with custom config:

```bash
python mt_ddos_monitor.py --config /path/to/config.yml
```

### API Endpoints

#### Get Status
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/status
```

#### Get Recent Events
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/events?hours=24
```

#### Block an IP
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "1.2.3.4", "reason": "Manual block"}' \
  http://localhost:5000/api/blocked-ips
```

#### Unblock an IP
```bash
curl -X DELETE -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/blocked-ips/1.2.3.4
```

### Web Dashboard

The React-based dashboard provides:

1. **Dashboard Tab**: Overview of current status and recent events
2. **Events Tab**: Detailed event history with filtering
3. **Blocked IPs Tab**: Manage blocked IP addresses

## ⚙️ Configuration

### Detection Settings

```yaml
detection:
  check_interval: 30              # Check every 30 seconds
  packet_threshold: 10000         # Packets per second
  auto_block_enabled: true        # Enable auto-blocking
  block_duration: "1h"            # Block for 1 hour
  address_list_name: "ddos_blocklist"
```

### Notification Settings

Configure email, webhook, or Telegram notifications:

```yaml
notifications:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    from_address: "alerts@example.com"
    to_addresses:
      - "admin@example.com"
```

## 🐳 Docker Deployment

The application includes Docker support with three services:

- **backend**: Python API server
- **frontend**: React web interface  
- **monitor**: Background monitoring service

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔒 Security

- **API Authentication**: All API endpoints require valid API key
- **Whitelist Support**: Protect trusted IPs from blocking
- **Secure Defaults**: Safe default configurations
- **No Hardcoded Credentials**: Use environment variables

See [SECURITY.md](SECURITY.md) for security best practices.

## 📊 Database Schema

Events are stored in SQLite with the following schema:

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    attack_type TEXT NOT NULL,
    source_ip TEXT NOT NULL,
    target_ip TEXT NOT NULL,
    packet_rate INTEGER NOT NULL,
    severity TEXT NOT NULL,
    action_taken TEXT NOT NULL
);
```

## 🧪 Testing

Run tests with pytest:

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=.
```

## 🛠️ Development

### Setting up Development Environment

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run linting
flake8 .

# Format code
black .

# Type checking
mypy .
```

### Frontend Development

```bash
cd frontend
npm install
npm start  # Development server on port 3000
npm run build  # Production build
```

## 📝 Logging

Logs are written to:
- **Console**: Real-time monitoring
- **File**: `mt_ddos_monitor.log` (rotating)

Configure logging in `config.yml`:

```yaml
logging:
  level: "INFO"
  file: "mt_ddos_monitor.log"
  max_size_mb: 100
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [librouteros](https://github.com/luqasz/librouteros) - RouterOS API library
- MikroTik community for RouterOS scripting examples
- Contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK/discussions)

## 🗺️ Roadmap

- [x] Support for multiple routers ✅ **NEW**
- [ ] Machine learning-based anomaly detection
- [ ] Grafana dashboard integration
- [ ] Advanced threat intelligence integration
- [ ] Mobile app for monitoring

## 📚 Documentation

For detailed documentation, see:
- [API Documentation](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

**Note**: This application is intended for legitimate network security purposes. Always ensure compliance with applicable laws and regulations.