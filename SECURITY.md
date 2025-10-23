# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it by emailing the maintainers directly. Do not open a public issue.

## Security Best Practices

### 1. Credentials Management

**Never commit credentials to the repository.**

- Use environment variables for sensitive data
- Store passwords in a secure password manager
- Rotate API keys regularly

Example using environment variables:

```bash
export MIKROTIK_PASSWORD="your-secure-password"
export API_KEY="your-secure-api-key"
```

### 2. API Key Security

The API key protects access to the monitoring endpoints:

```yaml
# config.yml
api:
  key: "${API_KEY}"  # Use environment variable
```

Set via environment:
```bash
export API_KEY="$(openssl rand -hex 32)"
```

### 3. Network Security

- **Firewall Rules**: Restrict API access to trusted networks
- **HTTPS/TLS**: Use SSL for production deployments
- **VPN**: Consider VPN access for remote management

### 4. MikroTik Router Security

- Enable API-SSL (port 8729) instead of plain API (port 8728)
- Create dedicated user for the monitoring application
- Use strong passwords (min 16 characters)
- Restrict API access by source IP

Example RouterOS configuration:

```routeros
# Create dedicated user
/user add name=ddos-monitor group=full password="strong-password"

# Enable API-SSL
/ip service set api-ssl disabled=no

# Restrict API access
/ip service set api address=192.168.88.0/24
/ip service set api-ssl address=192.168.88.0/24
```

### 5. Database Security

- Store database file in a secure location
- Regular backups with encryption
- Limit database file permissions

```bash
chmod 600 ddos_events.db
```

### 6. Docker Security

- Don't run containers as root
- Use read-only volumes where possible
- Keep images updated
- Scan images for vulnerabilities

```bash
# Scan for vulnerabilities
docker scan mt-ddos-backend

# Update images
docker-compose pull
docker-compose up -d
```

### 7. Logging Security

- Sanitize logs (don't log passwords)
- Secure log file permissions
- Regular log rotation
- Monitor logs for suspicious activity

### 8. Updates and Patches

- Keep dependencies updated
- Monitor for security advisories
- Test updates in staging first

```bash
# Update dependencies
pip list --outdated
pip install --upgrade -r requirements.txt
```

### 9. Whitelist Configuration

Always whitelist critical infrastructure:

```yaml
detection:
  whitelist:
    - "192.168.88.0/24"    # Management network
    - "10.0.0.1"           # Gateway
    - "8.8.8.8"            # DNS servers
```

### 10. Rate Limiting

Protect the API from abuse:

```yaml
api:
  rate_limit: 100  # requests per minute
```

## Security Checklist

Before deploying to production:

- [ ] All credentials moved to environment variables
- [ ] API key is strong and unique
- [ ] API-SSL enabled on MikroTik
- [ ] Firewall rules restrict access
- [ ] Database file permissions set correctly
- [ ] HTTPS/TLS configured for web access
- [ ] Whitelist configured appropriately
- [ ] Logging configured and monitored
- [ ] Docker images scanned for vulnerabilities
- [ ] Backup strategy implemented
- [ ] Incident response plan documented

## Known Security Considerations

### 1. RouterOS API Access

The application requires full API access to manage firewall rules. Create a dedicated user with minimal required permissions.

### 2. SQL Injection

The application uses parameterized queries to prevent SQL injection. Never concatenate user input into SQL queries.

### 3. Cross-Site Scripting (XSS)

The React frontend sanitizes all user input. Be cautious when displaying event data.

### 4. Rate Limiting

The API includes rate limiting, but consider using a reverse proxy (nginx) for additional protection.

## Incident Response

If a security incident occurs:

1. **Isolate**: Disconnect affected systems
2. **Assess**: Determine scope and impact
3. **Contain**: Implement immediate mitigations
4. **Eradicate**: Remove the threat
5. **Recover**: Restore normal operations
6. **Review**: Conduct post-incident analysis

## Compliance

This application may be subject to various security and privacy regulations depending on your jurisdiction. Ensure compliance with:

- GDPR (if processing EU data)
- Local data protection laws
- Industry-specific regulations

## Security Contacts

For security-related questions or concerns, contact the maintainers.

## Updates

This security policy is reviewed and updated regularly. Last updated: 2024-01-01
