# Deployment Guide

This guide covers various deployment scenarios for the MikroTik DDoS Monitor application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Manual Installation](#manual-installation)
4. [Production Deployment](#production-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

### Hardware Requirements

- **Minimum:**
  - CPU: 1 core
  - RAM: 512 MB
  - Storage: 1 GB

- **Recommended:**
  - CPU: 2+ cores
  - RAM: 2 GB
  - Storage: 10 GB (for logs and database)

### Software Requirements

- MikroTik Router with RouterOS 7.x
- Linux server (Ubuntu 20.04+ recommended)
- Docker 20.10+ and docker-compose 2.0+ (for containerized deployment)
- Python 3.11+ (for manual installation)
- Node.js 18+ (for frontend development)

### Network Requirements

- Network connectivity to MikroTik router
- RouterOS API enabled (port 8728 or 8729 for SSL)
- Firewall rules allowing API access

## Quick Start with Docker

### 1. Configure MikroTik Router

```bash
# Enable API
/ip service set api disabled=no

# Enable API-SSL (recommended for production)
/ip service set api-ssl disabled=no

# Create dedicated user
/user add name=ddos-monitor group=full password="strong-password"
```

### 2. Clone Repository

```bash
git clone https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK.git
cd DDDOS-MITIGATION-MIKROTIK
```

### 3. Configure Application

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano config.yml
```

Update the following in `config.yml`:
```yaml
mikrotik:
  host: "YOUR_ROUTER_IP"
  username: "ddos-monitor"
  password: "YOUR_PASSWORD"
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 5. Access Dashboard

Open your browser and navigate to:
- Frontend: http://localhost:3000
- API: http://localhost:5000/api/health

## Manual Installation

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git

# CentOS/RHEL
sudo yum install python311 python311-venv git
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Application

```bash
cp .env.example .env
nano config.yml  # Edit configuration
```

### 5. Import RouterOS Scripts

```bash
# Copy scripts/mikrotik-scripts.rsc to your router
# Then import via RouterOS terminal:
/import mikrotik-scripts.rsc
```

### 6. Run Application

```bash
# Start monitor
python mt_ddos_monitor.py &

# Start API
python api/app.py &
```

### 7. Setup as System Service

Create `/etc/systemd/system/mt-ddos-monitor.service`:

```ini
[Unit]
Description=MikroTik DDoS Monitor
After=network.target

[Service]
Type=simple
User=ddos-monitor
WorkingDirectory=/opt/mt-ddos-monitor
ExecStart=/opt/mt-ddos-monitor/venv/bin/python mt_ddos_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mt-ddos-monitor
sudo systemctl start mt-ddos-monitor
```

## Production Deployment

### 1. Use Environment Variables

Never hardcode credentials. Use environment variables:

```bash
export MIKROTIK_PASSWORD="$(openssl rand -base64 32)"
export API_KEY="$(openssl rand -hex 32)"
```

### 2. Enable SSL/TLS

#### For API (using nginx)

Install nginx:
```bash
sudo apt install nginx certbot python3-certbot-nginx
```

Configure nginx (`/etc/nginx/sites-available/mt-ddos`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

Get SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com
```

#### For MikroTik API

Update `config.yml`:
```yaml
mikrotik:
  port: 8729  # API-SSL port
  use_ssl: true
```

### 3. Database Backups

Set up automated backups:

```bash
#!/bin/bash
# /opt/mt-ddos-monitor/backup.sh

BACKUP_DIR="/var/backups/mt-ddos"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /opt/mt-ddos-monitor/ddos_events.db $BACKUP_DIR/ddos_events_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "ddos_events_*.db" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /opt/mt-ddos-monitor/backup.sh
```

### 4. Monitoring

Set up monitoring with systemd:

```bash
# Check status
systemctl status mt-ddos-monitor

# View logs
journalctl -u mt-ddos-monitor -f
```

Or use external monitoring:
- Prometheus + Grafana
- Datadog
- New Relic

### 5. Firewall Configuration

```bash
# Allow API access
sudo ufw allow 5000/tcp

# Allow frontend access
sudo ufw allow 3000/tcp

# Or allow nginx
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw enable
```

## Cloud Deployment

### AWS EC2

1. Launch EC2 instance (t3.small or larger)
2. Configure security groups:
   - Inbound: 22 (SSH), 80 (HTTP), 443 (HTTPS)
   - Outbound: All traffic
3. Install Docker and docker-compose
4. Clone repository and follow Docker deployment steps
5. Use Elastic IP for stable addressing
6. Configure Route53 for DNS

### Google Cloud Platform

1. Create Compute Engine instance
2. Configure firewall rules
3. Install Docker
4. Deploy using docker-compose
5. Use Cloud SQL for database (optional)

### DigitalOcean

1. Create Droplet (1 GB RAM minimum)
2. Use Docker one-click app
3. Deploy with docker-compose
4. Configure floating IP
5. Use managed database (optional)

### Docker Hub Deployment

Build and push images:

```bash
# Build images
docker build -t your-registry/mt-ddos-backend:latest .
docker build -f Dockerfile.frontend -t your-registry/mt-ddos-frontend:latest .

# Push to registry
docker push your-registry/mt-ddos-backend:latest
docker push your-registry/mt-ddos-frontend:latest

# Deploy on remote server
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check API health
curl http://localhost:5000/api/health

# Check service status
docker-compose ps

# Check logs
docker-compose logs --tail=100 -f
```

### Log Rotation

Configure logrotate (`/etc/logrotate.d/mt-ddos`):

```
/opt/mt-ddos-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 ddos-monitor ddos-monitor
    sharedscripts
    postrotate
        systemctl reload mt-ddos-monitor
    endscript
}
```

### Database Maintenance

```bash
# Compact database
sqlite3 ddos_events.db "VACUUM;"

# Check database size
du -h ddos_events.db

# Clean old events (older than 30 days)
sqlite3 ddos_events.db "DELETE FROM events WHERE timestamp < datetime('now', '-30 days');"
```

### Updates

```bash
# Backup current installation
cp -r /opt/mt-ddos-monitor /opt/mt-ddos-monitor.backup

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart services
docker-compose down
docker-compose up -d
```

### Troubleshooting

Common issues and solutions:

1. **Cannot connect to router**
   - Check firewall rules
   - Verify API is enabled
   - Test with: `/tool fetch url="http://router-ip:8728"`

2. **Database locked**
   - Check for multiple instances running
   - Ensure proper file permissions
   - Restart application

3. **High memory usage**
   - Check event retention settings
   - Vacuum database
   - Adjust check interval

4. **API not responding**
   - Check logs: `docker-compose logs backend`
   - Verify port is not in use: `netstat -tulpn | grep 5000`
   - Restart service

## Performance Tuning

### For High Traffic Networks

Update `config.yml`:

```yaml
detection:
  check_interval: 10  # More frequent checks
  packet_threshold: 50000  # Higher threshold

advanced:
  max_connections: 500000  # Increase limit
  event_buffer_mb: 200  # More memory for buffering
```

### Database Optimization

```bash
# Create indices
sqlite3 ddos_events.db << EOF
CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_source_ip ON events(source_ip);
CREATE INDEX IF NOT EXISTS idx_severity ON events(severity);
EOF
```

## Security Hardening

1. Use dedicated user account
2. Restrict file permissions
3. Enable SELinux/AppArmor
4. Use secrets management (Vault, AWS Secrets Manager)
5. Regular security updates
6. Network segmentation
7. Intrusion detection (fail2ban)

## Backup and Disaster Recovery

### Backup Strategy

1. **Database**: Daily backups, 30-day retention
2. **Configuration**: Version controlled in git
3. **Logs**: Shipped to external logging service

### Disaster Recovery

1. Keep configuration in version control
2. Document network topology
3. Test restore procedures monthly
4. Maintain off-site backups
5. Document recovery procedures

## Support

For deployment issues:
- Check logs first
- Review documentation
- Search existing issues
- Open new issue with details
