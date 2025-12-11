# Security Policy

## Overview

TravelNet Portal is designed with security as a primary concern. This document outlines the security measures implemented and best practices for secure deployment.

## Security Features

### 🔐 Authentication & Authorization
- **Secure Session Management**: Flask sessions with secure, httponly cookies
- **Rate Limiting**: Configurable request limits per IP address
- **Input Validation**: Comprehensive validation of all user inputs
- **Command Injection Prevention**: Whitelisted system commands only

### 🛡️ Network Security
- **Firewall Configuration**: UFW with restrictive default policies
- **Fail2ban Integration**: Automatic IP blocking for suspicious activity
- **Secure WiFi Configuration**: WPA2/WPA3 with strong default passwords
- **Network Isolation**: Proper VLAN and routing configuration

### 🔒 Application Security
- **CSRF Protection**: Built-in Flask CSRF protection
- **XSS Prevention**: Template auto-escaping and input sanitization
- **SQL Injection Prevention**: No direct database queries (uses system commands)
- **Secure Headers**: Security headers for all HTTP responses

### 📝 Logging & Monitoring
- **Comprehensive Logging**: All actions logged with timestamps and IP addresses
- **Log Rotation**: Automatic log rotation to prevent disk space issues
- **Security Event Logging**: Failed authentication attempts and suspicious activity

## Configuration Security

### Environment Variables
All sensitive configuration is stored in environment variables:

```bash
# Required - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secure-secret-key-here

# Optional - Customize as needed
APP_NAME="Your Portal Name"
DEFAULT_AP_SSID="Your-Network-Name"
DEFAULT_AP_PASSWORD="Your-Secure-Password"
```

### File Permissions
The setup script automatically sets secure file permissions:
- Configuration files: `600` (owner read/write only)
- Application directory: `755` (owner full, group/other read/execute)
- Log files: `644` (owner read/write, group/other read)

## Deployment Security

### Pre-Deployment Checklist
- [ ] Generate unique SECRET_KEY for production
- [ ] Change default access point password
- [ ] Configure firewall rules
- [ ] Enable fail2ban
- [ ] Set up SSH key authentication
- [ ] Disable password authentication for SSH
- [ ] Update all system packages

### Network Configuration
```bash
# Recommended firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 53
ufw allow 67/udp
```

### SSH Hardening
```bash
# /etc/ssh/sshd_config recommendations
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```

## Security Best Practices

### For Administrators
1. **Regular Updates**: Keep system packages updated
2. **Monitor Logs**: Regularly check application and system logs
3. **Backup Configuration**: Maintain secure backups of configuration files
4. **Network Monitoring**: Monitor for unusual network activity
5. **Access Control**: Limit physical access to the device

### For Users
1. **Strong Passwords**: Use strong, unique passwords for WiFi networks
2. **Secure Networks**: Only connect to trusted WiFi networks
3. **Regular Reboots**: Restart the device periodically
4. **Monitor Connections**: Check connected devices regularly

## Vulnerability Reporting

### Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

### Reporting Process
If you discover a security vulnerability, please:

1. **DO NOT** create a public GitHub issue
2. Email security details to: [security@your-domain.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline
- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Release**: Within 30 days (for critical issues)

## Security Updates

### Automatic Updates
The application includes automatic security update checking:
```bash
# Check for updates
./manage.sh update-check

# Apply security updates
./manage.sh security-update
```

### Manual Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
source /opt/travelnet/venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Incident Response

### In Case of Compromise
1. **Immediate Actions**:
   - Disconnect from internet
   - Change all passwords
   - Check logs for suspicious activity
   - Document the incident

2. **Recovery Steps**:
   - Restore from clean backup
   - Update all software
   - Regenerate all keys and passwords
   - Monitor for continued suspicious activity

3. **Prevention**:
   - Analyze root cause
   - Implement additional security measures
   - Update security procedures

## Compliance

### Standards Adherence
- **OWASP Top 10**: Protection against common web vulnerabilities
- **CIS Controls**: Implementation of critical security controls
- **NIST Framework**: Alignment with cybersecurity framework

### Privacy
- **Data Minimization**: Only collect necessary data
- **Local Processing**: All data processed locally, no external transmission
- **Log Retention**: Automatic log rotation and cleanup

## Security Testing

### Automated Testing
```bash
# Run security tests
python -m pytest tests/security/

# Check for known vulnerabilities
safety check

# Static code analysis
bandit -r app.py
```

### Manual Testing
- Regular penetration testing
- Code review for security issues
- Configuration audits
- Network security assessments

## Contact

For security-related questions or concerns:
- Email: security@your-domain.com
- GPG Key: [Your GPG Key ID]
- Response Time: 24-48 hours

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update your security measures.