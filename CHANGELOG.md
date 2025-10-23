# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-01

### Added
- Initial release of MikroTik DDoS Monitor & Auto-Actuator
- Real-time DDoS attack monitoring
- Automated IP blocking via RouterOS API
- SQLite database for event logging
- Flask-based REST API
- React-based web dashboard
- Docker and docker-compose support
- RouterOS firewall configuration scripts
- Multiple attack detection algorithms:
  - SYN flood detection
  - UDP flood detection
  - ICMP flood detection
  - Connection flooding detection
- Configurable thresholds and settings
- API key authentication
- Event severity classification (LOW, MEDIUM, HIGH, CRITICAL)
- Automatic and manual IP blocking
- Whitelist support for trusted IPs
- Health check endpoints
- Comprehensive documentation
- Unit tests and CI/CD pipeline

### Features
- **Monitoring**: Real-time traffic analysis with configurable intervals
- **Detection**: Multiple algorithm support for various attack types
- **Mitigation**: Auto-blocking with configurable timeout periods
- **API**: RESTful endpoints for all functionality
- **Dashboard**: User-friendly web interface
- **Logging**: Event history with filtering and search
- **Security**: API key authentication and secure defaults

### Documentation
- README.md with comprehensive setup guide
- SECURITY.md with security best practices
- CONTRIBUTING.md with contribution guidelines
- API documentation
- Configuration examples

### Configuration
- YAML-based configuration
- Environment variable support
- Docker configuration examples
- RouterOS script templates

## [Unreleased]

### Planned
- Machine learning-based anomaly detection
- Support for multiple routers
- Grafana dashboard integration
- Advanced threat intelligence integration
- Email/Webhook/Telegram notifications
- Mobile app for monitoring
- More sophisticated attack pattern detection
- Historical trend analysis
- GeoIP blocking capabilities
- Rate limiting enhancements

---

For full details, see the [commit history](https://github.com/fahim8401/DDDOS-MITIGATION-MIKROTIK/commits/main).
